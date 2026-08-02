from __future__ import annotations

from dataclasses import asdict
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.discovery.config_loader import load_icp_config
from app.discovery.engine import run_discovery_cycle
from app.discovery.repository import discovery_summary, get_run, list_runs, list_staging_records
from app.schemas import DiscoveryRunRead, DiscoveryRunRequest, DiscoveryStagingRead
from app.api.routes import require_write_api_key

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
    )


def _serialize_stage(record) -> DiscoveryStagingRead:
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
        qualification_status=record.qualification_status,
        score=record.score,
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


@router.get("/icp")
def get_icp_config():
    return {"product_lines": [asdict(icp) for icp in load_icp_config()]}


@router.post("/run")
def trigger_discovery(
    payload: DiscoveryRunRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    return run_discovery_cycle(db, product_names=payload.product_names, force=payload.force)


@router.get("/runs", response_model=list[DiscoveryRunRead])
def discovery_runs(db: Session = Depends(get_db)):
    return [_serialize_run(run) for run in list_runs(db, limit=100)]


@router.get("/runs/{run_id}", response_model=DiscoveryRunRead)
def discovery_run_detail(run_id: int, db: Session = Depends(get_db)):
    run = get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Discovery run not found")
    return _serialize_run(run)


@router.get("/staging", response_model=list[DiscoveryStagingRead])
def discovery_staging(db: Session = Depends(get_db)):
    return [_serialize_stage(record) for record in list_staging_records(db)]


@router.get("/manual-review", response_model=list[DiscoveryStagingRead])
def discovery_manual_review(db: Session = Depends(get_db)):
    return [_serialize_stage(record) for record in list_staging_records(db, manual_review_only=True)]


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    summary = discovery_summary(db)
    return {
        "manual_review_count": summary["manual_review_count"],
        "staging_count": summary["staging_count"],
        "runs": [_serialize_run(run) for run in summary["runs"]],
        "recent_manual_review": [_serialize_stage(record) for record in summary["recent_manual_review"]],
    }
