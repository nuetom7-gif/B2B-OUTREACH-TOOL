from __future__ import annotations

from dataclasses import asdict, replace
import json

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.base import Company, DiscoveryStagingRecord
from app.discovery.config_loader import load_icp_config
from app.discovery.engine import DiscoveryEngine, run_discovery_cycle
from app.discovery.repository import discovery_run_reasons, discovery_summary, get_run, list_runs, list_staging_records, list_staging_records_page
from app.schemas import (
    DiscoveryJobCreate,
    DiscoveryJobRead,
    DiscoveryManualReviewDecision,
    DiscoveryRunRead,
    DiscoveryRunReasonsRead,
    DiscoveryRunRequest,
    DiscoveryStagingRead,
    DiscoveryStagingPageRead,
    DiscoveryStagingSummaryRead,
)
from app.api.routes import require_write_api_key
from app.services.discovery_jobs import create_discovery_job, get_job, job_detail, list_jobs, request_cancel, submit_discovery_job
from app.services.discovery_merge import find_blocked_contact_for_discovery, upsert_company_from_discovery, upsert_contact_from_discovery
from app.services.outreach import add_audit

router = APIRouter(prefix="/discovery", tags=["discovery"])


def _review_time():
    return datetime.now(timezone.utc)


def _review_details(record: DiscoveryStagingRecord, decision: str, note: str) -> dict:
    try:
        details = json.loads(record.reason_details_json or "{}")
    except json.JSONDecodeError:
        details = {}
    details["manual_review"] = {
        "decision": decision,
        "note": note.strip(),
        "decided_at": _review_time().isoformat(),
    }
    return details


def _staging_profile_name(record: DiscoveryStagingRecord) -> str:
    try:
        payload = json.loads(record.qualification_input_json or "{}")
        profile = payload.get("icp", {}).get("profile_name")
        if profile:
            return str(profile)
    except (json.JSONDecodeError, AttributeError):
        pass
    return record.product_name


def _approve_staged_company(db: Session, record: DiscoveryStagingRecord) -> tuple[Company, int]:
    company = db.get(Company, record.crm_company_id) if record.crm_company_id else None
    if company is None:
        company, _, _ = upsert_company_from_discovery(
            db,
            company_payload={
                "name": record.company_name or "Unnamed company",
                "industry": record.industry or "Unspecified",
                "source": "apollo_auto",
                "source_provider": record.provider_name,
                "source_record_id": record.apollo_organization_id,
                "apollo_organization_id": record.apollo_organization_id,
                "notes": "Approved from discovery manual review.",
                "product_fits": [record.product_name],
                "last_sync": _review_time(),
                "sync_status": "synced",
                "needs_manual_review": False,
                "lead_score": record.score,
            },
            source_provider=record.provider_name,
        )
        record.crm_company_id = company.id

    company.needs_manual_review = False
    company.sync_status = "synced"

    contacts_imported = 0
    people = db.execute(
        select(DiscoveryStagingRecord).where(
            DiscoveryStagingRecord.run_id == record.run_id,
            DiscoveryStagingRecord.record_type == "person",
            DiscoveryStagingRecord.apollo_organization_id == record.apollo_organization_id,
        )
    ).scalars().all()
    for person in people:
        if person.crm_contact_id or not person.person_name:
            continue
        blocked = find_blocked_contact_for_discovery(
            db,
            company_name=company.name,
            source_provider=person.provider_name,
            source_record_id=record.apollo_organization_id,
            apollo_organization_id=record.apollo_organization_id,
            contact_source_record_id=person.apollo_person_id,
            apollo_person_id=person.apollo_person_id,
            email=person.person_email,
            name=person.person_name,
            title=person.person_title or "Unknown",
        )
        if blocked:
            person.final_status = "rejected"
            person.sync_status = "rejected"
            person.warning_message = "Existing do-not-contact contact blocked manual-review approval."
            continue
        contact, created, _ = upsert_contact_from_discovery(
            db,
            company=company,
            contact_payload={
                "name": person.person_name,
                "title": person.person_title or "Unknown",
                "source_record_id": person.apollo_person_id,
                "apollo_person_id": person.apollo_person_id,
                "email": person.person_email,
                "phone": person.person_phone,
                "linkedin_url": person.person_linkedin_url,
                "source": "apollo_auto",
                "source_provider": person.provider_name,
                "last_sync": _review_time(),
                "lead_score": person.score or record.score,
                "discovery_profile": _staging_profile_name(record),
            },
            source_provider=person.provider_name,
        )
        person.crm_company_id = company.id
        person.crm_contact_id = contact.id
        person.final_status = "approved"
        person.sync_status = "imported" if created else "updated"
        person.needs_manual_review = False
        contacts_imported += int(created)
    return company, contacts_imported


def _serialize_run(run) -> DiscoveryRunRead:
    return DiscoveryRunRead(
        id=run.id,
        product_name=run.product_name,
        search_frequency=run.search_frequency,
        status=run.status,
        started_at=run.started_at,
        ended_at=run.ended_at,
        duration_seconds=run.duration_seconds,
        companies_found=run.companies_found,
        companies_imported=run.companies_imported,
        companies_updated=run.companies_updated,
        companies_skipped=run.companies_skipped,
        contacts_found=run.contacts_found,
        contacts_imported=run.contacts_imported,
        contacts_updated=run.contacts_updated,
        contacts_skipped=run.contacts_skipped,
        api_calls_used=run.api_calls_used,
        quota_remaining=run.quota_remaining,
        errors=json.loads(run.errors_json or "[]"),
        warnings=json.loads(run.warnings_json or "[]"),
        qualification_summary=json.loads(run.qualification_summary_json or "{}"),
        qualification_top_failure_reasons=json.loads(run.qualification_top_failure_reasons_json or "[]"),
        qualification_average_score=run.qualification_average_score,
        qualification_evaluated_count=run.qualification_evaluated_count,
        qualification_imported_count=run.qualification_imported_count,
        qualification_manual_review_count=run.qualification_manual_review_count,
        qualification_rejected_count=run.qualification_rejected_count,
        reason_breakdown=json.loads(run.reason_breakdown_json or "{}"),
    )


def _serialize_stage(record) -> DiscoveryStagingRead:
    normalized_contacts = json.loads(record.normalized_contacts_json or "[]")
    if not isinstance(normalized_contacts, list):
        normalized_contacts = []
    return DiscoveryStagingRead(
        id=record.id,
        run_id=record.run_id,
        product_name=record.product_name,
        provider_name=record.provider_name,
        record_type=record.record_type,
        apollo_organization_id=record.apollo_organization_id,
        apollo_person_id=record.apollo_person_id,
        company_name=record.company_name,
        company_domain=record.company_domain,
        industry=record.industry,
        country=record.country,
        region=record.region,
        employee_count=record.employee_count,
        company_size=record.company_size,
        person_name=record.person_name,
        person_title=record.person_title,
        person_email=record.person_email,
        person_phone=record.person_phone,
        person_linkedin_url=record.person_linkedin_url,
        person_seniority=record.person_seniority,
        raw_organization=json.loads(record.raw_organization_json or "{}"),
        organization_mapping=json.loads(record.organization_mapping_json or "{}"),
        people_request=json.loads(record.people_request_json or "{}"),
        raw_people_response=json.loads(record.raw_people_response_json or "{}"),
        normalized_company=json.loads(record.normalized_company_json or "{}"),
        normalized_contacts=normalized_contacts,
        qualification_input=json.loads(record.qualification_input_json or "{}"),
        qualification_status=record.qualification_status,
        final_status=record.final_status,
        decision_stage=record.decision_stage,
        reason_category=record.reason_category,
        reason_details=json.loads(record.reason_details_json or "{}"),
        score=record.score,
        qualification_threshold=record.qualification_threshold,
        manual_review_threshold=record.manual_review_threshold,
        qualification_evaluated_at=record.qualification_evaluated_at,
        qualification_result=json.loads(record.qualification_result_json or "{}"),
        confidence=record.confidence,
        needs_manual_review=record.needs_manual_review,
        sync_status=record.sync_status,
        error_message=record.error_message,
        warning_message=record.warning_message,
        crm_company_id=record.crm_company_id,
        crm_contact_id=record.crm_contact_id,
        apollo_last_updated=record.apollo_last_updated,
        last_sync=record.last_sync,
    )


def _serialize_job(job) -> DiscoveryJobRead:
    return DiscoveryJobRead(
        id=job.id,
        product_segment=job.product_segment,
        industry=job.industry,
        country=job.country,
        state=job.state,
        city=job.city,
        keywords=job.keywords,
        company_limit=job.company_limit,
        contacts_per_company=job.contacts_per_company,
        max_leads=job.max_leads,
        status=job.status,
        current_step=job.current_step,
        progress_percent=job.progress_percent,
        companies_found=job.companies_found,
        companies_processed=job.companies_processed,
        contacts_discovered=job.contacts_discovered,
        qualified_leads=job.qualified_leads,
        imported_leads=job.imported_leads,
        skipped_leads=job.skipped_leads,
        failed_leads=job.failed_leads,
        api_calls_used=job.api_calls_used,
        quota_remaining=job.quota_remaining,
        request_json=job.request_json,
        result_json=job.result_json,
        error_message=job.error_message,
        started_at=job.started_at,
        ended_at=job.ended_at,
        cancelled_at=job.cancelled_at,
        cancel_requested=job.cancel_requested,
    )


@router.get("/icp")
def get_icp_config():
    profiles = load_icp_config()
    return {
        "product_lines": [asdict(icp) for icp in profiles],
        "search_profiles": [
            {
                "profile_name": icp.search_profile_name,
                "product_name": icp.product_name,
                "business_division": icp.business_division or icp.product_name,
                "target_segment": icp.target_segment or icp.search_profile_name,
                "enabled": icp.enabled,
                "countries": icp.locations or icp.country,
                "states": icp.states,
                "employee_min": icp.employee_min,
                "employee_max": icp.employee_max,
            }
            for icp in profiles
        ],
    }


@router.get("/search-profiles")
def get_search_profiles():
    profiles = load_icp_config()
    return [
        {
            "profile_name": icp.search_profile_name,
            "product_name": icp.product_name,
            "business_division": icp.business_division or icp.product_name,
            "target_segment": icp.target_segment or icp.search_profile_name,
            "enabled": icp.enabled,
            "countries": icp.locations or icp.country,
            "states": icp.states,
            "employee_min": icp.employee_min,
            "employee_max": icp.employee_max,
            "decision_makers": icp.target_titles,
            # Expose the configured criteria so clients can explain the
            # backend-owned Apollo search without duplicating its logic.
            "company_keywords": list(
                dict.fromkeys(icp.product_keywords + icp.manufacturing_keywords + icp.application_keywords)
            ),
            "apollo_industries": icp.apollo_industries or icp.exact_industries,
            "related_industries": icp.related_industries,
        }
        for icp in profiles
        if icp.enabled
    ]


@router.get("/search-builder")
def get_search_builder(profile_name: str, country: str | None = None, state: str | None = None, city: str | None = None, employee_min: int | None = None, employee_max: int | None = None):
    from app.discovery.search_builder import build_icp_search_request

    profile = next((icp for icp in load_icp_config() if icp.search_profile_name.lower() == profile_name.lower()), None)
    if profile is None:
        raise HTTPException(status_code=404, detail="Discovery search profile not found")
    return asdict(build_icp_search_request(profile, country=country, state=state, city=city, employee_min=employee_min, employee_max=employee_max))


@router.post("/run")
def trigger_discovery(
    payload: DiscoveryRunRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    if payload.profile_name:
        profile = next(
            (icp for icp in load_icp_config() if icp.search_profile_name.lower() == payload.profile_name.strip().lower()),
            None,
        )
        if profile is None or not profile.enabled:
            raise HTTPException(status_code=400, detail="Enabled discovery search profile not found")
        from app.core.config import get_settings

        settings = get_settings()
        job_request = DiscoveryJobCreate(
            profile_name=profile.search_profile_name,
            product_segment=profile.search_profile_name,
            industry=profile.target_segment or profile.search_profile_name,
            country=payload.country or (profile.country[0] if profile.country else "India"),
            state=payload.state,
            city=payload.city,
            company_limit=settings.apollo_max_companies_per_run,
            contacts_per_company=settings.apollo_max_contacts_per_company,
            max_leads=settings.apollo_max_companies_per_run * settings.apollo_max_contacts_per_company,
        )
        job = create_discovery_job(db, payload=job_request)
        submit_discovery_job(job.id, job_request)
        return {"job": _serialize_job(job), "queued": True}

    custom_fields = {
        "product_segment",
        "industry",
        "country",
        "state",
        "keywords",
        "company_limit",
        "contacts_per_company",
        "max_leads",
    }
    if payload.model_fields_set.intersection(custom_fields):
        if not payload.product_segment or not payload.industry or not payload.country:
            raise HTTPException(status_code=400, detail="product_segment, industry, and country are required")
        job_request = DiscoveryJobCreate(
            product_segment=payload.product_segment,
            industry=payload.industry,
            country=payload.country,
            state=payload.state,
            keywords=payload.keywords or "",
            company_limit=payload.company_limit or 30,
            contacts_per_company=payload.contacts_per_company or 2,
            max_leads=payload.max_leads or 60,
        )
        job = create_discovery_job(db, payload=job_request)
        submit_discovery_job(job.id, job_request)
        return {"job": _serialize_job(job), "queued": True}
    return run_discovery_cycle(db, product_names=payload.product_names, force=payload.force)


@router.get("/runs", response_model=list[DiscoveryRunRead])
def discovery_runs(db: Session = Depends(get_db)):
    return [_serialize_run(run) for run in list_runs(db, limit=100)]


@router.get("/jobs", response_model=list[DiscoveryJobRead])
def discovery_jobs(db: Session = Depends(get_db)):
    return [_serialize_job(job) for job in list_jobs(db)]


@router.get("/jobs/{job_id}")
def discovery_job(job_id: int, db: Session = Depends(get_db)):
    detail = job_detail(db, job_id)
    return {
        "job": _serialize_job(detail["job"]),
        "logs": [
            {
                "id": log.id,
                "job_id": log.job_id,
                "level": log.level,
                "message": log.message,
                "metadata_json": log.metadata_json,
                "created_at": log.created_at,
            }
            for log in detail["logs"]
        ],
    }


@router.post("/jobs/{job_id}/cancel", response_model=DiscoveryJobRead)
def cancel_discovery_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    try:
        job = request_cancel(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize_job(job)


@router.get("/runs/{run_id}", response_model=DiscoveryRunRead)
def discovery_run_detail(run_id: int, db: Session = Depends(get_db)):
    run = get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Discovery run not found")
    return _serialize_run(run)


@router.get("/runs/{run_id}/reasons", response_model=DiscoveryRunReasonsRead)
def discovery_run_reasons_detail(run_id: int, db: Session = Depends(get_db)):
    try:
        return discovery_run_reasons(db, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/runs/{run_id}/records", response_model=DiscoveryStagingPageRead)
def discovery_run_reason_records(
    run_id: int,
    reason_category: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = list_staging_records_page(
        db,
        run_id=run_id,
        reason_category=reason_category,
        limit=limit,
        offset=offset,
    )
    return {"items": [_serialize_stage_summary(item) for item in items], "total": total, "limit": limit, "offset": offset}


def _serialize_stage_summary(payload: dict) -> DiscoveryStagingSummaryRead:
    return DiscoveryStagingSummaryRead.model_validate(payload)


@router.get("/staging", response_model=DiscoveryStagingPageRead)
def discovery_staging_page(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = list_staging_records_page(db, limit=limit, offset=offset)
    return {"items": [_serialize_stage_summary(item) for item in items], "total": total, "limit": limit, "offset": offset}


@router.get("/staging/{record_id}", response_model=DiscoveryStagingRead)
def discovery_staging_detail(record_id: int, db: Session = Depends(get_db)):
    record = db.get(DiscoveryStagingRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Discovery staging record not found")
    return _serialize_stage(record)


@router.get("/manual-review", response_model=DiscoveryStagingPageRead)
def discovery_manual_review(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = list_staging_records_page(db, manual_review_only=True, limit=limit, offset=offset)
    return {"items": [_serialize_stage_summary(item) for item in items], "total": total, "limit": limit, "offset": offset}


@router.post("/staging/{record_id}/review")
def decide_manual_review(
    record_id: int,
    payload: DiscoveryManualReviewDecision,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    decision = payload.decision.strip().lower()
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="decision must be approve or reject")
    record = db.get(DiscoveryStagingRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Discovery staging record not found")
    if not record.needs_manual_review:
        raise HTTPException(status_code=409, detail="This record has already been reviewed")
    if record.record_type != "organization":
        raise HTTPException(status_code=400, detail="Only organization records can be decided from the research queue")

    contacts_imported = 0
    company = db.get(Company, record.crm_company_id) if record.crm_company_id else None
    if decision == "approve":
        company, contacts_imported = _approve_staged_company(db, record)
        record.final_status = "approved"
        record.sync_status = "imported"
        record.warning_message = "Approved during manual review."
    else:
        if company and company.needs_manual_review:
            company.needs_manual_review = False
            company.sync_status = "rejected"
        record.final_status = "rejected"
        record.sync_status = "rejected"
        record.warning_message = "Rejected during manual review."

    record.needs_manual_review = False
    record.decision_stage = "manual_review"
    record.reason_details_json = json.dumps(_review_details(record, decision, payload.note), default=str)
    record.last_sync = _review_time()
    add_audit(
        db,
        entity_type="discovery_staging_record",
        entity_id=str(record.id),
        action="manual_review_approved" if decision == "approve" else "manual_review_rejected",
        reason="Discovery record approved during manual review." if decision == "approve" else "Discovery record rejected during manual review.",
        metadata={"record_id": record.id, "note": payload.note.strip(), "contacts_imported": contacts_imported},
        company_id=company.id if company else None,
    )
    db.commit()
    db.refresh(record)
    return {"record": _serialize_stage(record), "contacts_imported": contacts_imported}


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    summary = discovery_summary(db)
    return {
        "manual_review_count": summary["manual_review_count"],
        "staging_count": summary["staging_count"],
        "runs": [_serialize_run(run) for run in summary["runs"]],
        "recent_manual_review": [_serialize_stage(record) for record in summary["recent_manual_review"]],
        "latest_qualification_summary": summary["latest_qualification_summary"],
        "qualification_metrics": summary["qualification_metrics"],
    }
