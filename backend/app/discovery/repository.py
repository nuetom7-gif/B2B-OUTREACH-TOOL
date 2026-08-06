from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from collections import Counter, defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.discovery.types import (
    DiscoveryCompanyCandidate,
    DiscoveryContactCandidate,
    DiscoveryContext,
    ICPProductLine,
)
from app.models.base import DiscoveryJob, DiscoveryRun, DiscoveryStagingRecord


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
        final_status="staged",
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
        final_status="staged",
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


def list_staging_records_for_reason(
    db: Session,
    *,
    run_id: int,
    reason_category: str | None = None,
) -> list[DiscoveryStagingRecord]:
    stmt = select(DiscoveryStagingRecord).where(DiscoveryStagingRecord.run_id == run_id)
    if reason_category:
        stmt = stmt.where(DiscoveryStagingRecord.reason_category == reason_category)
    stmt = stmt.order_by(DiscoveryStagingRecord.created_at.desc())
    return db.execute(stmt).scalars().all()


def todays_api_calls_used(db: Session) -> int:
    start = now_utc().replace(hour=0, minute=0, second=0, microsecond=0)
    run_calls = db.scalar(
        select(func.coalesce(func.sum(DiscoveryRun.api_calls_used), 0)).where(DiscoveryRun.started_at >= start)
    ) or 0
    job_calls = db.scalar(
        select(func.coalesce(func.sum(DiscoveryJob.api_calls_used), 0)).where(DiscoveryJob.started_at >= start)
    ) or 0
    return run_calls + job_calls


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
    latest_run = runs[0] if runs else None
    staging_records = list_staging_records(db)
    failure_counter: Counter[str] = Counter()
    bonus_counter: Counter[str] = Counter()
    penalty_counter: Counter[str] = Counter()
    industry_counter: Counter[str] = Counter()
    keyword_counter: Counter[str] = Counter()
    cluster_counter: Counter[str] = Counter()
    decision_counter: Counter[str] = Counter()
    product_scores: defaultdict[str, list[float]] = defaultdict(list)
    icp_scores: defaultdict[str, list[float]] = defaultdict(list)
    status_counter: Counter[str] = Counter()
    total_scores: list[float] = []

    for record in staging_records:
        payload = {}
        try:
            payload = json.loads(record.qualification_result_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        if not payload:
            continue
        score = float(payload.get("final_score", record.score or 0))
        total_scores.append(score)
        status = str(payload.get("final_status") or record.final_status or record.qualification_status or "unknown")
        status_counter[status] += 1
        product_scores[record.product_name].append(score)
        icp_scores[record.product_name].append(score)
        for rule in payload.get("rule_results", []):
            if isinstance(rule, dict) and float(rule.get("points_awarded", 0) or 0) <= 0:
                failure_counter[str(rule.get("rule_name") or "Unknown Rule")] += 1
        for item in payload.get("applied_bonuses", []):
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "Bonus")
            bonus_counter[label] += 1
            category = str(item.get("category") or "")
            matched_value = item.get("matched_value")
            if category == "industry" and matched_value:
                industry_counter[str(matched_value)] += 1
            if category.startswith("keyword") and matched_value:
                keyword_counter[str(matched_value)] += 1
            if category == "cluster" and matched_value:
                cluster_counter[str(matched_value)] += 1
            if category == "decision_maker" and matched_value:
                decision_counter[str(matched_value)] += 1
        for item in payload.get("applied_penalties", []):
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "Penalty")
            penalty_counter[label] += 1
        if payload.get("matched_industry_name"):
            industry_counter[str(payload["matched_industry_name"])] += 1
        for keyword in payload.get("matched_keywords", []) or []:
            keyword_counter[str(keyword)] += 1
        if payload.get("matched_cluster"):
            cluster_counter[str(payload["matched_cluster"])] += 1
        if payload.get("matched_decision_maker_title"):
            decision_counter[str(payload["matched_decision_maker_title"])] += 1

    average_score = round(sum(total_scores) / len(total_scores), 2) if total_scores else 0.0

    def _avg_map(values: defaultdict[str, list[float]]) -> dict[str, float]:
        return {key: round(sum(scores) / len(scores), 2) for key, scores in values.items() if scores}

    return {
        "runs": runs,
        "manual_review_count": len(manual_review),
        "staging_count": db.scalar(select(func.count(DiscoveryStagingRecord.id))) or 0,
        "recent_manual_review": manual_review[:25],
        "latest_qualification_summary": json.loads(latest_run.qualification_summary_json or "{}") if latest_run else {},
        "qualification_metrics": {
            "average_score": average_score,
            "status_counts": dict(status_counter),
            "most_common_failure_reasons": [{"label": label, "count": count} for label, count in failure_counter.most_common(10)],
            "most_common_bonuses": [{"label": label, "count": count} for label, count in bonus_counter.most_common(10)],
            "most_common_penalties": [{"label": label, "count": count} for label, count in penalty_counter.most_common(10)],
            "most_matched_industries": [{"label": label, "count": count} for label, count in industry_counter.most_common(10)],
            "most_matched_keywords": [{"label": label, "count": count} for label, count in keyword_counter.most_common(15)],
            "top_manufacturing_clusters": [{"label": label, "count": count} for label, count in cluster_counter.most_common(10)],
            "top_decision_maker_titles": [{"label": label, "count": count} for label, count in decision_counter.most_common(10)],
            "average_score_per_icp": _avg_map(icp_scores),
            "average_score_per_product_line": _avg_map(product_scores),
        },
    }


def discovery_run_reasons(db: Session, run_id: int) -> dict:
    run = get_run(db, run_id)
    if run is None:
        raise ValueError("Discovery run not found")

    records = list_staging_records_for_reason(db, run_id=run_id)
    total_candidates_found = len(records)
    imported_count = sum(1 for record in records if record.final_status == "imported")
    final_status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    imported_reason_counts: Counter[str] = Counter()

    for record in records:
        final_status_counts[str(record.final_status or "unknown")] += 1
        category = str(record.reason_category or "unknown")
        if record.final_status == "imported":
            imported_reason_counts[category] += 1
        else:
            reason_counts[category] += 1

    return {
        "run_id": run_id,
        "product_name": run.product_name,
        "status": run.status,
        "total_candidates_found": total_candidates_found,
        "imported_count": imported_count,
        "reason_counts": [{"reason_category": category, "count": count} for category, count in reason_counts.most_common()],
        "success_counts": [{"reason_category": category, "count": count} for category, count in imported_reason_counts.most_common()],
        "final_status_counts": [{"final_status": status, "count": count} for status, count in final_status_counts.most_common()],
    }
