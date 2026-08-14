from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime
from threading import Event, Lock
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import session as db_session
from app.discovery.contact_strategy import discover_contacts_for_organization
from app.discovery.config_loader import load_icp_config
from app.discovery.engine import DiscoveryEngine, run_discovery_cycle
from app.discovery.provider_manager import create_default_provider_manager
from app.discovery.qualification import score_organization, score_person
from app.discovery.repository import todays_api_calls_used
from app.discovery.types import ICPProductLine
from app.models.base import DiscoveryJob, DiscoveryJobLog
from app.schemas import DiscoveryJobCreate
from app.services.discovery_merge import (
    find_blocked_contact_for_discovery,
    upsert_company_from_discovery,
    upsert_contact_from_discovery,
)
from app.services.outreach import now_utc


class DiscoveryJobCancelled(RuntimeError):
    pass


_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="discovery-job")
_CANCEL_EVENTS: dict[int, Event] = {}
_EVENT_LOCK = Lock()


def _job_cancel_event(job_id: int) -> Event:
    with _EVENT_LOCK:
        event = _CANCEL_EVENTS.get(job_id)
        if event is None:
            event = Event()
            _CANCEL_EVENTS[job_id] = event
        return event


def _drop_job_cancel_event(job_id: int) -> None:
    with _EVENT_LOCK:
        _CANCEL_EVENTS.pop(job_id, None)


def _provider_calls_used(provider_manager) -> int:
    total = 0
    for provider in getattr(provider_manager, "enabled_providers", lambda: [])():
        total += int(getattr(provider, "api_calls_used", 0) or 0)
    return total


def _log_job(db: Session, job: DiscoveryJob, level: str, message: str, metadata: dict[str, Any] | None = None) -> None:
    db.add(
        DiscoveryJobLog(
            job_id=job.id,
            level=level,
            message=message,
            metadata_json=json.dumps(metadata or {}, default=str),
        )
    )


def _parse_keywords(keywords: str | None) -> list[str]:
    if not keywords:
        return []
    return [item.strip() for item in keywords.replace(";", ",").split(",") if item.strip()]


def _build_icp(request: DiscoveryJobCreate) -> ICPProductLine:
    base = next(
        (
            item
            for item in load_icp_config()
            if item.search_profile_name.lower() == (request.profile_name or request.product_segment).lower()
            or item.product_name.lower() == request.product_segment.lower()
        ),
        None,
    )
    if base is None:
        raise ValueError(f"Unknown product segment: {request.product_segment}")

    if request.profile_name:
        return replace(
            base,
            country=[request.country] if request.country else base.country,
            states=[request.state] if request.state else base.states,
            cities=[request.city] if request.city else base.cities,
        )
    merged_keywords = list(dict.fromkeys(base.company_keywords + _parse_keywords(request.keywords) + [request.industry]))
    return ICPProductLine(
        product_name=base.product_name,
        enabled=True,
        country=[request.country] if request.country else base.country,
        regions=[request.state] if request.state else base.regions,
        target_industries=[request.industry] if request.industry else base.target_industries,
        exclude_industries=base.exclude_industries,
        company_keywords=merged_keywords,
        exclude_keywords=base.exclude_keywords,
        apollo_filters=dict(base.apollo_filters),
        employee_min=base.employee_min,
        employee_max=base.employee_max,
        company_size=list(base.company_size),
        preferred_company_types=list(base.preferred_company_types),
        target_titles=list(base.target_titles),
        preferred_titles=list(base.preferred_titles),
        decision_level=list(base.decision_level),
        lead_score_rules=dict(base.lead_score_rules),
        search_frequency="On Demand",
        priority=base.priority,
        states=[request.state] if request.state else base.states,
        cities=[request.city] if request.city else base.cities,
    )


def run_profile_discovery_job(db: Session, job: DiscoveryJob, request: DiscoveryJobCreate) -> DiscoveryJob:
    job.status = "running"
    job.current_step = "Running configured discovery profile"
    job.started_at = now_utc()
    db.commit()
    try:
        icp = _build_icp(request)
        result = DiscoveryEngine(db).run_product_line(icp)
        job.status = "completed" if result.get("status") == "completed" else "failed"
        job.current_step = "Completed" if job.status == "completed" else "Failed"
        job.progress_percent = 100
        job.companies_found = int(result.get("companies_found", 0) or 0)
        job.companies_processed = job.companies_found
        job.contacts_discovered = int(result.get("contacts_found", 0) or 0)
        job.imported_leads = int(result.get("contacts_imported", 0) or 0)
        job.api_calls_used = int(result.get("api_calls_used", 0) or 0)
        job.result_json = json.dumps(result, default=str)
        if result.get("error"):
            job.error_message = str(result["error"])
    except Exception as exc:
        job.status = "failed"
        job.current_step = "Failed"
        job.error_message = str(exc)
        job.result_json = json.dumps({"status": "failed", "error": str(exc)}, default=str)
    finally:
        job.ended_at = now_utc()
        db.commit()
    return job


def create_discovery_job(db: Session, payload: DiscoveryJobCreate) -> DiscoveryJob:
    job = DiscoveryJob(
        product_segment=payload.product_segment,
        industry=payload.industry,
        country=payload.country,
        state=payload.state,
        city=payload.city,
        keywords=payload.keywords or "",
        company_limit=payload.company_limit,
        contacts_per_company=payload.contacts_per_company,
        max_leads=payload.max_leads,
        status="pending",
        current_step="queued",
        progress_percent=0,
        request_json=json.dumps(payload.model_dump(), default=str),
    )
    db.add(job)
    db.flush()
    _log_job(db, job, "info", "Discovery job queued.", payload.model_dump())
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int) -> DiscoveryJob | None:
    return db.get(DiscoveryJob, job_id)


def list_jobs(db: Session, limit: int = 100) -> list[DiscoveryJob]:
    return db.execute(select(DiscoveryJob).order_by(DiscoveryJob.created_at.desc()).limit(limit)).scalars().all()


def job_detail(db: Session, job_id: int) -> dict[str, Any]:
    job = db.get(DiscoveryJob, job_id)
    if job is None:
        raise ValueError("Discovery job not found")
    logs = (
        db.execute(select(DiscoveryJobLog).where(DiscoveryJobLog.job_id == job_id).order_by(DiscoveryJobLog.created_at.asc()))
        .scalars()
        .all()
    )
    return {
        "job": job,
        "logs": logs,
    }


def request_cancel(db: Session, job_id: int) -> DiscoveryJob:
    job = db.get(DiscoveryJob, job_id)
    if job is None:
        raise ValueError("Discovery job not found")
    job.cancel_requested = True
    _job_cancel_event(job_id).set()
    _log_job(db, job, "warning", "Cancellation requested from UI.", {})
    db.commit()
    db.refresh(job)
    return job


def _check_cancel(job: DiscoveryJob, db: Session, cancel_event: Event) -> None:
    if cancel_event.is_set() or job.cancel_requested:
        job.status = "cancelled"
        job.cancelled_at = now_utc()
        _log_job(db, job, "warning", "Job cancelled.", {"job_id": job.id})
        db.commit()
        raise DiscoveryJobCancelled()


def run_targeted_discovery_job(
    db: Session,
    job: DiscoveryJob,
    request: DiscoveryJobCreate,
    *,
    cancel_event: Event | None = None,
) -> DiscoveryJob:
    if request.profile_name:
        return run_profile_discovery_job(db, job, request)
    settings = get_settings()
    cancel_event = cancel_event or _job_cancel_event(job.id)
    provider_manager = create_default_provider_manager()
    start_calls = _provider_calls_used(provider_manager)

    job.status = "running"
    job.current_step = "Preparing Apollo search"
    job.started_at = now_utc()
    job.cancel_requested = False
    db.flush()
    _log_job(db, job, "info", "Discovery job started.", request.model_dump())
    db.commit()

    try:
        icp = _build_icp(request)
        companies_limit = max(1, request.company_limit)
        contacts_limit = max(1, request.max_leads)
        contacts_per_company = max(1, request.contacts_per_company)
        page = 1
        per_page = max(10, min(100, companies_limit))

        def _before_search() -> None:
            used = todays_api_calls_used(db) + (_provider_calls_used(provider_manager) - start_calls)
            if used >= settings.apollo_daily_call_limit:
                raise RuntimeError("Apollo daily call limit reached")

        while job.companies_processed < companies_limit and job.imported_leads < contacts_limit:
            _check_cancel(job, db, cancel_event)
            job.current_step = f"Searching Apollo companies page {page}"
            organizations = provider_manager.search_organizations(icp, page=page, per_page=per_page)
            job.companies_found += len(organizations)
            job.api_calls_used = _provider_calls_used(provider_manager) - start_calls
            job.quota_remaining = max(0, settings.apollo_daily_call_limit - todays_api_calls_used(db) - job.api_calls_used)
            if not organizations:
                break

            for organization in organizations:
                _check_cancel(job, db, cancel_event)
                if job.companies_processed >= companies_limit or job.imported_leads >= contacts_limit:
                    break

                job.companies_processed += 1
                job.current_step = f"Qualifying {organization.name}"
                contact_batch = discover_contacts_for_organization(
                    provider_manager,
                    icp,
                    organization,
                    max_contacts=contacts_per_company,
                    per_page=contacts_per_company,
                    before_search=_before_search,
                )
                job.contacts_discovered += len(contact_batch.contacts)
                job.api_calls_used = _provider_calls_used(provider_manager) - start_calls
                job.quota_remaining = max(0, settings.apollo_daily_call_limit - todays_api_calls_used(db) - job.api_calls_used)
                people = contact_batch.contacts

                org_score = score_organization(icp, organization, people)
                if org_score.status != "qualified":
                    job.skipped_leads += 1
                    _log_job(
                        db,
                        job,
                        "info",
                        f"Organization skipped: {organization.name}",
                        {"status": org_score.status, "reasons": org_score.reasons},
                    )
                    job.progress_percent = min(99, int((job.companies_processed / companies_limit) * 100))
                    db.commit()
                    continue

                company_payload = {
                    "name": organization.name,
                    "industry": organization.industry or request.industry,
                    "source": "apollo_auto",
                    "source_provider": organization.source_provider,
                    "source_record_id": organization.source_record_id,
                    "notes": organization.description or "",
                    "product_fits": [request.product_segment],
                    "apollo_organization_id": organization.provider_organization_id,
                    "apollo_last_updated": organization.last_updated,
                    "last_sync": now_utc(),
                    "sync_status": "synced",
                    "needs_manual_review": False,
                    "lead_score": int(org_score.score),
                }
                company, _, _ = upsert_company_from_discovery(
                    db,
                    company_payload=company_payload,
                    source_provider=organization.source_provider,
                )
                company.lead_score = max(company.lead_score, int(org_score.score))
                company.apollo_organization_id = company.apollo_organization_id or organization.provider_organization_id
                company.source_provider = company.source_provider or organization.source_provider
                company.source_record_id = company.source_record_id or organization.source_record_id
                company.apollo_last_updated = organization.last_updated or company.apollo_last_updated
                company.last_sync = now_utc()
                company.sync_status = "synced"
                company.needs_manual_review = False
                company.discovery_contacts_returned = contact_batch.total_contacts_returned
                company.contact_status = contact_batch.contact_status
                company.fallback_contact_used = contact_batch.fallback_contact_used

                if not people:
                    company.contact_status = "No Contact Found"
                    company.fallback_contact_used = contact_batch.fallback_contact_used

                for person in people:
                    _check_cancel(job, db, cancel_event)
                    person_score = score_person(icp, person)
                    blocked_contact = find_blocked_contact_for_discovery(
                        db,
                        company_name=organization.name,
                        source_provider=organization.source_provider,
                        source_record_id=organization.source_record_id,
                        apollo_organization_id=organization.provider_organization_id,
                        contact_source_record_id=person.provider_person_id,
                        apollo_person_id=person.provider_person_id,
                        email=person.email,
                        name=person.name,
                        title=person.title,
                    )
                    if blocked_contact:
                        job.skipped_leads += 1
                        _log_job(
                            db,
                            job,
                            "warning",
                            "Lead blocked by Do Not Contact rule.",
                            {"contact_id": blocked_contact.id, "contact_name": blocked_contact.name},
                        )
                        continue

                    contact_payload = {
                        "name": person.name,
                        "title": person.title,
                        "source_record_id": person.provider_person_id,
                        "apollo_person_id": person.provider_person_id,
                        "verification_status": person.email_status or "unknown",
                        "last_sync": now_utc(),
                        "lead_score": int(org_score.score + person_score.score),
                        "email": person.email,
                        "phone": person.phone,
                        "linkedin_url": person.linkedin_url,
                        "source": "apollo_auto",
                        "source_provider": person.source_provider,
                        "contact_priority": person.contact_priority,
                        "recommended_primary_contact": person.recommended_primary_contact,
                        "fallback_contact_used": person.fallback_contact_used,
                        "contact_selection_reason": person.contact_selection_reason,
                    }
                    contact, created_contact, merged_fields = upsert_contact_from_discovery(
                        db,
                        company=company,
                        contact_payload=contact_payload,
                        source_provider=person.source_provider,
                    )
                    contact.apollo_person_id = contact.apollo_person_id or person.provider_person_id
                    contact.source_provider = contact.source_provider or person.source_provider
                    contact.source_record_id = contact.source_record_id or person.source_record_id
                    contact.verification_status = person.email_status or contact.verification_status
                    contact.last_sync = now_utc()
                    contact.lead_score = max(contact.lead_score, int(org_score.score + person_score.score))
                    contact.contact_priority = contact.contact_priority or person.contact_priority
                    contact.recommended_primary_contact = bool(contact.recommended_primary_contact or person.recommended_primary_contact)
                    contact.fallback_contact_used = bool(contact.fallback_contact_used or person.fallback_contact_used)
                    contact.contact_selection_reason = contact.contact_selection_reason or person.contact_selection_reason
                    if person_score.status == "qualified":
                        job.qualified_leads += 1
                    job.imported_leads += 1
                    _log_job(
                        db,
                        job,
                        "info",
                        "Lead imported from Apollo.",
                        {"contact_id": contact.id, "created": created_contact, "merged_fields": merged_fields},
                    )

                job.progress_percent = min(99, int((job.companies_processed / companies_limit) * 100))
                db.commit()

            if len(organizations) < per_page:
                break
            page += 1

        job.status = "completed"
        job.current_step = "Completed"
        job.progress_percent = 100
        _log_job(
            db,
            job,
            "info",
            "Discovery job completed.",
            {"companies_processed": job.companies_processed, "imported_leads": job.imported_leads},
        )
    except DiscoveryJobCancelled:
        job.current_step = "Cancelled"
    except Exception as exc:  # pragma: no cover - defensive boundary
        job.status = "failed"
        job.error_message = str(exc)
        job.current_step = "Failed"
        job.failed_leads += 1
        _log_job(db, job, "error", "Discovery job failed.", {"error": str(exc)})
    finally:
        job.ended_at = now_utc()
        job.api_calls_used = max(job.api_calls_used, _provider_calls_used(provider_manager) - start_calls)
        job.quota_remaining = max(0, settings.apollo_daily_call_limit - todays_api_calls_used(db) - job.api_calls_used)
        if job.status == "running":
            job.status = "completed"
            job.progress_percent = 100
        job.result_json = json.dumps(
            {
                "status": job.status,
                "companies_found": job.companies_found,
                "companies_processed": job.companies_processed,
                "contacts_discovered": job.contacts_discovered,
                "qualified_leads": job.qualified_leads,
                "imported_leads": job.imported_leads,
                "skipped_leads": job.skipped_leads,
                "failed_leads": job.failed_leads,
                "api_calls_used": job.api_calls_used,
                "quota_remaining": job.quota_remaining,
            },
            default=str,
        )
        db.commit()
        provider_manager.close()
        _drop_job_cancel_event(job.id)
    return job


def submit_discovery_job(job_id: int, request: DiscoveryJobCreate) -> None:
    cancel_event = _job_cancel_event(job_id)

    def _task() -> None:
        db = db_session.SessionLocal()
        try:
            job = db.get(DiscoveryJob, job_id)
            if job is None:
                return
            run_targeted_discovery_job(db, job, request, cancel_event=cancel_event)
        finally:
            db.close()

    _EXECUTOR.submit(_task)


def sync_legacy_discovery(db: Session, *, product_names: list[str] | None = None, force: bool = False) -> list[dict[str, Any]]:
    return run_discovery_cycle(db, product_names=product_names, force=force)
