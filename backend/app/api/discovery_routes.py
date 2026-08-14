from __future__ import annotations

from dataclasses import asdict, replace
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.base import DiscoveryStagingRecord
from app.discovery.config_loader import load_icp_config
from app.discovery.engine import DiscoveryEngine, run_discovery_cycle
from app.discovery.repository import discovery_run_reasons, discovery_summary, get_run, list_runs, list_staging_records, list_staging_records_page
from app.schemas import (
    DiscoveryJobCreate,
    DiscoveryJobRead,
    DiscoveryRunRead,
    DiscoveryRunReasonsRead,
    DiscoveryRunRequest,
    DiscoveryStagingRead,
    DiscoveryStagingPageRead,
    DiscoveryStagingSummaryRead,
)
from app.api.routes import require_write_api_key
from app.services.discovery_jobs import create_discovery_job, get_job, job_detail, list_jobs, request_cancel, submit_discovery_job

router = APIRouter(prefix="/discovery", tags=["discovery"])


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
def get_search_builder(profile_name: str, country: str | None = None, state: str | None = None, employee_min: int | None = None, employee_max: int | None = None):
    from app.discovery.search_builder import build_icp_search_request

    profile = next((icp for icp in load_icp_config() if icp.search_profile_name.lower() == profile_name.lower()), None)
    if profile is None:
        raise HTTPException(status_code=404, detail="Discovery search profile not found")
    return asdict(build_icp_search_request(profile, country=country, state=state, employee_min=employee_min, employee_max=employee_max))


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
