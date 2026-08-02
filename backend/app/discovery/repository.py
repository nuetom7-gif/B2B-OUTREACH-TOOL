from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.discovery.types import (
    DiscoveryCompanyCandidate,
    DiscoveryContactCandidate,
    DiscoveryContext,
    ICPProductLine,
)
from app.models.base import DiscoveryRun, DiscoveryStagingRecord


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _to_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _encode(value) -> str:
    return json.dumps(value, default=str)


def _decode_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        payload = json.loads(value)
        return payload if isinstance(payload, list) else []
    except json.JSONDecodeError:
        return []


def create_run(db: Session, icp: ICPProductLine) -> DiscoveryRun:
    run = DiscoveryRun(
        product_name=icp.product_name,
        search_frequency=icp.search_frequency,
        status="running",
        started_at=now_utc(),
    )
    db.add(run)
    db.flush()
    return run


def finish_run(
    db: Session,
    run: DiscoveryRun,
    *,
    context: DiscoveryContext | None = None,
    status: str = "completed",
) -> DiscoveryRun:
    run.status = status
    run.ended_at = now_utc()
    if run.started_at:
        run.duration_seconds = max(0, int((_to_aware(run.ended_at) - _to_aware(run.started_at)).total_seconds()))
    if context:
        run.api_calls_used = context.api_calls_used
        run.quota_remaining = context.quota_remaining
        run.errors_json = _encode(context.errors)
        run.warnings_json = _encode(context.warnings)
    return run


def stage_organization(
    db: Session,
    run: DiscoveryRun,
    icp: ICPProductLine,
    organization: DiscoveryCompanyCandidate,
) -> DiscoveryStagingRecord:
    record = DiscoveryStagingRecord(
        run_id=run.id,
        product_name=icp.product_name,
        provider_name=organization.source_provider,
        record_type="organization",
        apollo_organization_id=organization.source_record_id,
        company_name=organization.name,
        company_domain=organization.domain,
        industry=organization.industry,
        country=organization.country,
        region=organization.region,
        employee_count=organization.employee_count,
        company_size=organization.company_size,
        raw_payload_json=_encode(organization.source_metadata),
        qualification_status="staged",
        confidence="unknown",
        sync_status="staged",
        apollo_last_updated=organization.last_updated,
    )
    db.add(record)
    db.flush()
    return record


def stage_person(
    db: Session,
    run: DiscoveryRun,
    icp: ICPProductLine,
    organization: DiscoveryCompanyCandidate,
    person: DiscoveryContactCandidate,
) -> DiscoveryStagingRecord:
    record = DiscoveryStagingRecord(
        run_id=run.id,
        product_name=icp.product_name,
        provider_name=person.source_provider,
        record_type="person",
        apollo_organization_id=organization.source_record_id,
        apollo_person_id=person.source_record_id,
        company_name=organization.name,
        company_domain=organization.domain,
        industry=organization.industry,
        country=person.country or organization.country,
        region=person.region or organization.region,
        employee_count=organization.employee_count,
        company_size=organization.company_size,
        person_name=person.name,
        person_title=person.title,
        person_email=person.email,
        person_phone=person.phone,
        person_linkedin_url=person.linkedin_url,
        person_seniority=person.seniority,
        raw_payload_json=_encode(person.source_metadata),
        qualification_status="staged",
        confidence="unknown",
        sync_status="staged",
        apollo_last_updated=organization.last_updated,
    )
    db.add(record)
    db.flush()
    return record


def get_run(db: Session, run_id: int) -> DiscoveryRun | None:
    return db.get(DiscoveryRun, run_id)


def list_runs(db: Session, limit: int = 50) -> list[DiscoveryRun]:
    return db.execute(select(DiscoveryRun).order_by(DiscoveryRun.started_at.desc()).limit(limit)).scalars().all()


def list_staging_records(db: Session, *, run_id: int | None = None, manual_review_only: bool = False) -> list[DiscoveryStagingRecord]:
    stmt = select(DiscoveryStagingRecord).order_by(DiscoveryStagingRecord.created_at.desc())
    if run_id is not None:
        stmt = stmt.where(DiscoveryStagingRecord.run_id == run_id)
    if manual_review_only:
        stmt = stmt.where(DiscoveryStagingRecord.needs_manual_review.is_(True))
    return db.execute(stmt).scalars().all()


def todays_api_calls_used(db: Session) -> int:
    start = now_utc().replace(hour=0, minute=0, second=0, microsecond=0)
    return db.scalar(
        select(func.coalesce(func.sum(DiscoveryRun.api_calls_used), 0)).where(DiscoveryRun.started_at >= start)
    ) or 0


def due_for_frequency(last_started_at: datetime | None, search_frequency: str) -> bool:
    if last_started_at is None:
        return True
    now = now_utc()
    search_frequency = search_frequency.lower()
    if search_frequency == "daily":
        return last_started_at < now - timedelta(days=1)
    if search_frequency == "weekly":
        return last_started_at < now - timedelta(days=7)
    if search_frequency == "monthly":
        return last_started_at < now - timedelta(days=30)
    return True


def latest_run_for_product(db: Session, product_name: str) -> DiscoveryRun | None:
    return (
        db.execute(
            select(DiscoveryRun)
            .where(DiscoveryRun.product_name == product_name)
            .order_by(DiscoveryRun.started_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


def discovery_summary(db: Session) -> dict:
    runs = list_runs(db, limit=100)
    manual_review = list_staging_records(db, manual_review_only=True)
    return {
        "runs": runs,
        "manual_review_count": len(manual_review),
        "staging_count": db.scalar(select(func.count(DiscoveryStagingRecord.id))) or 0,
        "recent_manual_review": manual_review[:25],
    }
