from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.discovery.apollo_provider import ApolloProviderError
from app.discovery.confidence import evaluate_discovery_confidence
from app.discovery.diagnostics import save_raw_organization_json
from app.discovery.config_loader import load_icp_config
from app.discovery.provider import DiscoveryProvider
from app.discovery.provider_manager import DiscoveryProviderManager, create_default_provider_manager
from app.discovery.search_strategy import optimize_search_strategies, plan_search_strategies
from app.discovery.contact_strategy import ContactDiscoveryBatch, discover_contacts_for_organization
from app.discovery.qualification import score_organization, score_person, summarize_qualification_results
from app.discovery.repository import (
    create_run,
    due_for_frequency,
    discovery_run_reasons,
    finish_run,
    latest_run_for_product,
    now_utc,
    stage_organization,
    stage_person,
    todays_api_calls_used,
)
from app.discovery.types import DiscoveryContext, ICPProductLine, ProviderOrganization, ProviderPerson
from app.models.base import Contact
from app.services.discovery_merge import (
    find_blocked_contact_for_discovery,
    upsert_company_from_discovery,
    upsert_contact_from_discovery,
)


class DiscoveryQuotaExceeded(RuntimeError):
    pass


def _json_payload(value: Any) -> str:
    return json.dumps(value, default=str)


def _has_company_identifier(organization: ProviderOrganization) -> bool:
    raw = organization.source_metadata or {}
    if isinstance(raw.get("apollo_raw_record"), dict):
        raw = raw["apollo_raw_record"]
    return bool(
        organization.domain
        or raw.get("linkedin_url")
        or raw.get("linkedin_url_normalized")
    )


def _crm_contact_has_phone(db: Session, apollo_person_id: str | None) -> bool:
    """Avoid paying to reveal a phone number the CRM already has."""
    if not str(apollo_person_id or "").strip():
        return False
    phone = db.execute(
        select(Contact.phone).where(Contact.apollo_person_id == apollo_person_id)
    ).scalar_one_or_none()
    return bool(str(phone or "").strip())


def _qualification_payload(
    *,
    run_id: int,
    organization,
    person=None,
    score_result,
    reason_category: str,
    decision_stage: str,
    reason_details: dict[str, Any],
    final_status: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "company": {
            "name": organization.name,
            "provider_name": organization.source_provider,
            "provider_record_id": organization.source_record_id,
            "apollo_organization_id": organization.provider_organization_id,
        },
        "run_id": run_id,
        "icp_profile_name": organization.source_metadata.get("icp_profile_name") if organization.source_metadata else None,
        "final_status": final_status or score_result.status,
        "final_score": score_result.score,
        "qualification_threshold": score_result.qualification_threshold,
        "manual_review_threshold": score_result.manual_review_threshold,
        "evaluation_timestamp": score_result.evaluation_timestamp,
        "overall_recommendation": score_result.overall_recommendation,
        "final_confidence": score_result.final_confidence,
        "matched_industry_level": score_result.matched_industry_level,
        "matched_industry_name": score_result.matched_industry_name,
        "matched_keywords": score_result.matched_keywords,
        "matched_keyword_groups": score_result.matched_keyword_groups,
        "matched_decision_maker": score_result.matched_decision_maker,
        "matched_decision_maker_title": score_result.matched_decision_maker_title,
        "matched_cluster": score_result.matched_cluster,
        "applied_bonuses": [asdict(item) for item in score_result.applied_bonuses],
        "applied_penalties": [asdict(item) for item in score_result.applied_penalties],
        "reasons": score_result.reasons,
        "rule_results": [asdict(rule_result) for rule_result in score_result.rule_results],
        "reason_category": reason_category,
        "decision_stage": decision_stage,
        "reason_details": reason_details,
        "total_contacts_returned": getattr(score_result, "total_contacts_returned", 0),
        "selected_contact_name": getattr(score_result, "selected_contact_name", None),
        "selected_contact_title": getattr(score_result, "selected_contact_title", None),
        "selected_contact_priority": getattr(score_result, "selected_contact_priority", None),
        "selected_contact_reason": getattr(score_result, "selected_contact_reason", None),
        "fallback_contact_used": getattr(score_result, "fallback_contact_used", False),
    }
    if person is not None:
        payload["person"] = {
            "name": person.name,
            "title": person.title,
            "provider_record_id": person.provider_person_id,
        }
    return payload


def _store_outcome(
    record,
    *,
    run_id: int,
    organization,
    score_result,
    reason_category: str,
    decision_stage: str,
    reason_details: dict[str, Any],
    person=None,
    final_status: str | None = None,
    sync_status: str | None = None,
    qualification_status: str | None = None,
) -> None:
    resolved_final_status = final_status or score_result.status
    record.qualification_status = qualification_status or score_result.status
    record.final_status = resolved_final_status
    record.decision_stage = decision_stage
    record.reason_category = reason_category
    record.reason_details_json = _json_payload(reason_details)
    if sync_status is not None:
        record.sync_status = sync_status
    record.qualification_result_json = _json_payload(
        _qualification_payload(
            run_id=run_id,
            organization=organization,
            person=person,
            score_result=score_result,
            reason_category=reason_category,
            decision_stage=decision_stage,
            reason_details=reason_details,
            final_status=resolved_final_status,
        )
    )


def _organization_reason_category(organization, org_score) -> tuple[str, dict[str, Any]]:
    rule_map = {rule.rule_name: rule for rule in org_score.rule_results}
    reason_details: dict[str, Any] = {
        "score": org_score.score,
        "qualification_threshold": org_score.qualification_threshold,
        "manual_review_threshold": org_score.manual_review_threshold,
        "reasons": org_score.reasons,
        "matched_industry_level": org_score.matched_industry_level,
        "matched_industry_name": org_score.matched_industry_name,
        "matched_keywords": org_score.matched_keywords,
        "matched_decision_maker_title": org_score.matched_decision_maker_title,
        "matched_cluster": org_score.matched_cluster,
    }
    if not organization.name or not organization.source_record_id:
        reason_details["missing_fields"] = [field for field, value in {"name": organization.name, "source_record_id": organization.source_record_id}.items() if not value]
        return "provider_error", reason_details
    if org_score.status == "qualified":
        return "imported", reason_details
    if rule_map.get("Industry Match") and rule_map["Industry Match"].points_awarded <= 0 and not org_score.matched_keywords:
        return "industry_mismatch", reason_details
    if rule_map.get("Employee Count") and rule_map["Employee Count"].points_awarded <= 0 and organization.employee_count is not None:
        reason_details["employee_count"] = organization.employee_count
        reason_details["qualification_threshold"] = org_score.qualification_threshold
        return "size_mismatch", reason_details
    if org_score.score < (org_score.qualification_threshold or 0):
        reason_details["score"] = org_score.score
        reason_details["threshold"] = org_score.qualification_threshold
        return "score_below_threshold", reason_details
    if org_score.status == "manual_review":
        return "score_below_threshold", reason_details
    return "provider_error", reason_details


def _person_reason_category(person, person_score, *, blocked_contact=None, qualification_threshold: float | None = None) -> tuple[str, dict[str, Any]]:
    rule_map = {rule.rule_name: rule for rule in person_score.rule_results}
    reason_details: dict[str, Any] = {
        "score": person_score.score,
        "qualification_threshold": qualification_threshold or person_score.qualification_threshold,
        "manual_review_threshold": person_score.manual_review_threshold,
        "reasons": person_score.reasons,
        "matched_decision_maker_title": person_score.matched_decision_maker_title,
        "matched_keywords": person_score.matched_keywords,
        "email_status": person.email_status,
        "person_title": person.title,
    }
    if blocked_contact is not None:
        reason_details["blocked_contact_id"] = blocked_contact.id
        reason_details["blocked_contact_name"] = blocked_contact.name
        return "duplicate_suppressed", reason_details
    if not person.name or not person.title:
        reason_details["missing_fields"] = [field for field, value in {"name": person.name, "title": person.title}.items() if not value]
        return "provider_error", reason_details
    if not person_score.matched_decision_maker_title:
        return "no_matching_title", reason_details
    if not person.email_status or person.email_status.lower() != "verified":
        if rule_map.get("Verified Email") and rule_map["Verified Email"].points_awarded <= 0:
            return "no_verified_email", reason_details
    if person_score.status == "qualified":
        return "imported", reason_details
    if person_score.score < (qualification_threshold or person_score.qualification_threshold or 0):
        reason_details["threshold"] = qualification_threshold or person_score.qualification_threshold
        return "score_below_threshold", reason_details
    if person_score.status == "manual_review":
        return "score_below_threshold", reason_details
    return "provider_error", reason_details


class DiscoveryEngine:
    def __init__(
        self,
        db: Session,
        provider: DiscoveryProvider | None = None,
        provider_manager: DiscoveryProviderManager | None = None,
    ) -> None:
        self.db = db
        self.settings = get_settings()
        if provider_manager is not None:
            self.provider_manager = provider_manager
        elif provider is not None:
            self.provider_manager = DiscoveryProviderManager(
                providers={provider.provider_name(): provider},
                enabled_provider_names=[provider.provider_name()],
            )
        else:
            self.provider_manager = create_default_provider_manager()

    def close(self) -> None:
        close = getattr(self.provider_manager, "close", None)
        if callable(close):
            close()

    def run_due(self, *, product_names: list[str] | None = None, force: bool = False) -> list[dict]:
        runs: list[dict] = []
        product_lines = [icp for icp in load_icp_config() if icp.enabled]
        if product_names:
            wanted = {name.lower() for name in product_names}
            product_lines = [icp for icp in product_lines if icp.product_name.lower() in wanted]
        product_lines.sort(key=lambda item: (item.priority, item.product_name.lower()))
        for icp in product_lines:
            last_run = latest_run_for_product(self.db, icp.product_name)
            if not force and last_run and not due_for_frequency(last_run.started_at, icp.search_frequency):
                continue
            runs.append(self.run_product_line(icp))
        return runs

    def _ensure_quota(self, context: DiscoveryContext) -> None:
        used_today = todays_api_calls_used(self.db)
        remaining = self.settings.apollo_daily_call_limit - used_today - context.api_calls_used
        context.quota_remaining = max(0, remaining)
        if remaining <= 0:
            raise DiscoveryQuotaExceeded("Apollo daily call limit reached")

    def _increment_calls(self, context: DiscoveryContext) -> None:
        context.api_calls_used += 1
        used_today = todays_api_calls_used(self.db)
        context.quota_remaining = max(0, self.settings.apollo_daily_call_limit - used_today - context.api_calls_used)

    def _publish_progress(self, run, context: DiscoveryContext) -> None:
        """Make an active run visible to the monitoring UI between checkpoints."""
        run.api_calls_used = context.api_calls_used
        run.quota_remaining = context.quota_remaining
        self.db.commit()

    def run_product_line(self, icp: ICPProductLine) -> dict:
        run = create_run(self.db, icp)
        context = DiscoveryContext(product_line=icp, run_id=run.id)
        # The background worker needs this row committed before the browser can monitor it.
        self._publish_progress(run, context)
        try:
            company_records: list[tuple[ProviderOrganization, object, ContactDiscoveryBatch, list[object]]] = []
            organization_scores = []
            imported_company_count = 0
            enrichment_attempted = 0
            enrichment_succeeded = 0
            enrichment_no_match = 0
            organization_enrichment_attempted = 0
            organization_enrichment_succeeded = 0
            organization_enrichment_no_match = 0
            strategy_metrics: dict[str, dict[str, Any]] = {}
            per_page = 100
            max_companies = self.settings.apollo_max_companies_per_run
            seen_companies: set[str] = set()
            for strategy in optimize_search_strategies(icp, plan_search_strategies(icp)):
                strategy_metrics[strategy.name] = {
                    "strategy_name": strategy.name,
                    "industries_used": [strategy.industry] if strategy.industry else [],
                    "keyword_used": strategy.product_keyword,
                    "companies_returned": 0,
                    "companies_merged": 0,
                    "companies_filtered": 0,
                    "companies_manual_review": 0,
                    "companies_qualified": 0,
                    "companies_imported": 0,
                    "confidence_scores": [],
                    "qualification_scores": [],
                }
                org_page = 1
                while len(company_records) < max_companies:
                    self._ensure_quota(context)
                    organizations = self.provider_manager.search_organizations_for_strategy(
                        icp, strategy, page=org_page, per_page=per_page
                    )
                    self._increment_calls(context)
                    if not organizations:
                        break
                    strategy_metrics[strategy.name]["companies_returned"] += len(organizations)
                    for organization in organizations:
                        if len(company_records) >= max_companies:
                            break
                        dedupe_key = (
                            organization.provider_organization_id
                            or (organization.domain or "").lower()
                            or organization.name.lower()
                        )
                        if dedupe_key in seen_companies:
                            strategy_metrics[strategy.name]["companies_merged"] += 1
                            continue
                        seen_companies.add(dedupe_key)
                        run.companies_found += 1
                        organization.source_metadata.setdefault("icp_profile_name", icp.search_profile_name)
                        organization.source_metadata["search_strategy"] = strategy.to_metadata()
                        if _has_company_identifier(organization):
                            organization_enrichment_attempted += 1
                            self._ensure_quota(context)
                            enriched_organization = self.provider_manager.enrich_organization(organization)
                            self._increment_calls(context)
                            if enriched_organization is None:
                                organization_enrichment_no_match += 1
                                organization.source_metadata["organization_enrichment_status"] = "no_match"
                            else:
                                organization_enrichment_succeeded += 1
                                organization = enriched_organization
                                organization.source_metadata["organization_enrichment_status"] = "enriched"
                        raw_response = organization.source_metadata.get("apollo_raw_response")
                        if self.settings.discovery_diagnostic_mode and isinstance(raw_response, dict):
                            organization.source_metadata["raw_organization_file"] = save_raw_organization_json(
                                run_id=run.id,
                                organization_id=organization.provider_organization_id,
                                payload=raw_response,
                            )
                        org_record = stage_organization(self.db, run, icp, organization)
                        confidence_result = evaluate_discovery_confidence(icp, organization, strategy)
                        strategy_metrics[strategy.name]["confidence_scores"].append(confidence_result["score"])
                        org_record.reason_details_json = _json_payload({"discovery_confidence": confidence_result})
                        org_record.warning_message = "; ".join(confidence_result["reasons"])
                        if not _has_company_identifier(organization):
                            strategy_metrics[strategy.name]["companies_manual_review"] += 1
                            org_record.qualification_status = "manual_review"
                            org_record.final_status = "manual_review"
                            org_record.decision_stage = "discovery_confidence"
                            org_record.reason_category = "missing_company_identifier"
                            org_record.sync_status = "manual_review"
                            org_record.needs_manual_review = True
                            org_record.warning_message = (
                                "Apollo returned no company domain or LinkedIn URL; manual identifier review is required."
                            )
                            company_records.append(
                                (organization, org_record, ContactDiscoveryBatch(organization=organization), [])
                            )
                            self._publish_progress(run, context)
                            continue
                        if confidence_result["confidence_band"] == "Low Relevance":
                            strategy_metrics[strategy.name]["companies_filtered"] += 1
                            org_record.qualification_status = "filtered"
                            org_record.final_status = "filtered"
                            org_record.decision_stage = "discovery_confidence"
                            org_record.reason_category = "low_discovery_confidence"
                            org_record.sync_status = "rejected"
                            company_records.append((organization, org_record, ContactDiscoveryBatch(organization=organization), []))
                            self._publish_progress(run, context)
                            continue
                        contact_batch, person_records = self._collect_people_for_org(icp, organization, run, context)
                        primary = contact_batch.primary_contact
                        if primary is not None and (
                            primary.recommended_primary_contact
                            or primary.contact_priority in {"tier_1", "tier_2", "tier_3", "tier_4"}
                        ):
                            enrichment_attempted += 1
                            self._ensure_quota(context)
                            enriched = self.provider_manager.enrich_person(
                                primary,
                                reveal_phone_number=not _crm_contact_has_phone(
                                    self.db, primary.provider_person_id
                                ),
                            )
                            self._increment_calls(context)
                            if enriched is None:
                                enrichment_no_match += 1
                            else:
                                enrichment_succeeded += 1
                                contact_batch.contacts = [
                                    enriched if contact.provider_person_id == primary.provider_person_id else contact
                                    for contact in contact_batch.contacts
                                ]
                                contact_batch.primary_contact = enriched
                        org_record.people_request_json = _json_payload(contact_batch.diagnostic_requests)
                        org_record.raw_people_response_json = _json_payload(contact_batch.diagnostic_responses)
                        org_record.normalized_contacts_json = _json_payload(
                            [person.source_metadata.get("normalized_contact", {}) for person in contact_batch.contacts]
                        )
                        org_record.warning_message = contact_batch.zero_contact_reason
                        company_records.append((organization, org_record, contact_batch, person_records))
                        self._publish_progress(run, context)
                    if len(organizations) < per_page:
                        break
                    org_page += 1

            for organization, org_record, contact_batch, person_records in company_records:
                if org_record.final_status == "filtered" or org_record.reason_category == "missing_company_identifier":
                    run.companies_skipped += 1
                    self._publish_progress(run, context)
                    continue
                people = contact_batch.contacts
                org_record.qualification_input_json = _json_payload(
                    {"icp": asdict(icp), "company": asdict(organization), "contacts": [asdict(person) for person in people]}
                )
                org_score = score_organization(icp, organization, people)
                strategy_name = (organization.source_metadata.get("search_strategy") or {}).get("name")
                if strategy_name in strategy_metrics:
                    strategy_metrics[strategy_name]["qualification_scores"].append(org_score.score)
                    if org_score.status == "qualified":
                        strategy_metrics[strategy_name]["companies_qualified"] += 1
                organization_scores.append(org_score)
                org_record.score = int(org_score.score)
                org_record.needs_manual_review = org_score.needs_manual_review
                org_record.confidence = org_score.final_confidence.lower() if org_score.final_confidence else (
                    "high" if org_score.status == "qualified" else "medium" if org_score.status == "manual_review" else "low"
                )
                org_record.qualification_status = org_score.status
                org_record.qualification_threshold = int(org_score.qualification_threshold or 0)
                org_record.manual_review_threshold = int(org_score.manual_review_threshold or 0)
                org_record.qualification_evaluated_at = org_score.evaluation_timestamp
                reason_category, reason_details = _organization_reason_category(organization, org_score)
                discovery_details = json.loads(org_record.reason_details_json or "{}")
                reason_details["discovery_confidence"] = discovery_details.get("discovery_confidence", {})
                org_record.warning_message = "; ".join(org_score.reasons) if org_score.reasons else None
                confidence_band = discovery_details.get("discovery_confidence", {}).get("confidence_band")
                keep_for_recall = confidence_band in {
                    "High Confidence",
                    "Good Prospect",
                    "Potential Prospect",
                }
                if org_score.status != "qualified" and not keep_for_recall:
                    _store_outcome(
                        org_record,
                        run_id=run.id,
                        organization=organization,
                        score_result=org_score,
                        reason_category=reason_category,
                        decision_stage="qualification",
                        reason_details=reason_details,
                        final_status=org_score.status,
                        sync_status="manual_review" if org_score.status == "manual_review" else "rejected",
                        qualification_status=org_score.status,
                    )
                    run.companies_skipped += 1
                    if org_score.needs_manual_review:
                        run.warnings_json = json.dumps((json.loads(run.warnings_json) if run.warnings_json else []) + [organization.name])
                    continue

                company_payload = {
                    "name": organization.name,
                    "industry": organization.industry or "Unspecified",
                    "source": "apollo_auto",
                    "source_provider": organization.source_provider,
                    "source_record_id": organization.source_record_id,
                    "notes": organization.description or "",
                    "product_fits": [icp.product_name],
                    "apollo_organization_id": organization.provider_organization_id,
                    "apollo_last_updated": organization.last_updated,
                    "last_sync": now_utc(),
                    "sync_status": "synced",
                    "needs_manual_review": org_score.status != "qualified",
                    "lead_score": int(org_score.score),
                }
                company, created, merged_fields = upsert_company_from_discovery(
                    self.db,
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
                company.needs_manual_review = org_score.status != "qualified"
                company.discovery_contacts_returned = contact_batch.total_contacts_returned
                company.contact_status = contact_batch.contact_status
                company.fallback_contact_used = contact_batch.fallback_contact_used
                org_record.crm_company_id = company.id
                org_record.last_sync = now_utc()
                import_reason_category = (
                    "qualification_manual_review"
                    if org_score.status != "qualified"
                    else "duplicate_merged"
                    if merged_fields
                    else "imported"
                )
                import_reason_details = {
                    "created": created,
                    "merged_fields": merged_fields,
                    "company_id": company.id,
                    "company_name": company.name,
                    "discovery_confidence": discovery_details.get("discovery_confidence", {}),
                }
                _store_outcome(
                    org_record,
                    run_id=run.id,
                    organization=organization,
                    score_result=org_score,
                    reason_category=import_reason_category,
                    decision_stage="import",
                    reason_details=import_reason_details,
                    final_status="imported",
                    sync_status=(
                        "manual_review"
                        if org_score.status != "qualified"
                        else "imported" if created else "updated" if merged_fields else "skipped"
                    ),
                    qualification_status=org_score.status,
                )
                imported_company_count += 1
                if strategy_name in strategy_metrics:
                    strategy_metrics[strategy_name]["companies_imported"] += 1
                if created:
                    run.companies_imported += 1
                elif merged_fields:
                    run.companies_updated += 1
                else:
                    run.companies_skipped += 1

                if not people:
                    company.contact_status = "No Contact Found"
                    company.fallback_contact_used = contact_batch.fallback_contact_used

                for person, person_record in zip(people, person_records):
                    person_record.qualification_input_json = _json_payload(
                        {"icp": asdict(icp), "company": asdict(organization), "contact": asdict(person)}
                    )
                    person_score = score_person(icp, person)
                    contact_score = int(org_score.score + person_score.score)
                    person_record.score = contact_score
                    person_record.needs_manual_review = False
                    person_record.confidence = person_score.final_confidence.lower() if person_score.final_confidence else (
                        "high" if contact_score >= int(icp.lead_score_rules.get("import_threshold", 60)) else "medium" if contact_score >= int(icp.lead_score_rules.get("manual_review_threshold", 35)) else "low"
                    )
                    person_record.qualification_status = "qualified"
                    person_record.warning_message = "; ".join(person_score.reasons) if person_score.reasons else None
                    person_record.qualification_threshold = int(person_score.qualification_threshold or 0)
                    person_record.manual_review_threshold = int(person_score.manual_review_threshold or 0)
                    person_record.qualification_evaluated_at = person_score.evaluation_timestamp
                    blocked_contact = find_blocked_contact_for_discovery(
                        self.db,
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
                        reason_category, reason_details = _person_reason_category(person, person_score, blocked_contact=blocked_contact)
                        _store_outcome(
                            person_record,
                            run_id=run.id,
                            organization=organization,
                            person=person,
                            score_result=person_score,
                            reason_category=reason_category,
                            decision_stage="duplicate_check",
                            reason_details=reason_details,
                            final_status="rejected",
                            sync_status="rejected",
                            qualification_status="rejected",
                        )
                        person_record.needs_manual_review = False
                        person_record.warning_message = "Existing do-not-contact contact blocked discovery import."
                        run.contacts_skipped += 1
                        run.warnings_json = json.dumps(
                            (json.loads(run.warnings_json) if run.warnings_json else [])
                            + [f"Blocked do-not-contact contact: {blocked_contact.name} ({blocked_contact.id})"]
                        )
                        continue
                    contact_payload = {
                        "name": person.name,
                        "title": person.title,
                        "source_record_id": person.provider_person_id,
                        "apollo_person_id": person.provider_person_id,
                        "verification_status": person.email_status or "unknown",
                        "last_sync": now_utc(),
                        "lead_score": contact_score,
                        "email": person.email,
                        "phone": person.phone,
                        "linkedin_url": person.linkedin_url,
                        "source": "apollo_auto",
                        "source_provider": person.source_provider,
                        "contact_priority": person.contact_priority,
                        "recommended_primary_contact": person.recommended_primary_contact,
                        "fallback_contact_used": person.fallback_contact_used,
                        "contact_selection_reason": person.contact_selection_reason,
                        "discovery_profile": icp.search_profile_name,
                    }
                    contact, created_contact, merged_contact_fields = upsert_contact_from_discovery(
                        self.db,
                        company=company,
                        contact_payload=contact_payload,
                        source_provider=person.source_provider,
                    )
                    contact.apollo_person_id = contact.apollo_person_id or person.provider_person_id
                    contact.source_provider = contact.source_provider or person.source_provider
                    contact.source_record_id = contact.source_record_id or person.source_record_id
                    contact.verification_status = person.email_status or contact.verification_status
                    contact.last_sync = now_utc()
                    contact.lead_score = max(contact.lead_score, contact_score)
                    contact.contact_priority = contact.contact_priority or person.contact_priority
                    contact.recommended_primary_contact = bool(contact.recommended_primary_contact or person.recommended_primary_contact)
                    contact.fallback_contact_used = bool(contact.fallback_contact_used or person.fallback_contact_used)
                    contact.contact_selection_reason = contact.contact_selection_reason or person.contact_selection_reason
                    person_record.crm_contact_id = contact.id
                    person_record.last_sync = now_utc()
                    reason_category, reason_details = _person_reason_category(
                        person,
                        person_score,
                        qualification_threshold=int(icp.lead_score_rules.get("import_threshold", 60)),
                    )
                    import_reason_category = "duplicate_merged" if merged_contact_fields else "imported"
                    import_reason_details = {
                        "created": created_contact,
                        "merged_fields": merged_contact_fields,
                        "contact_id": contact.id,
                        "contact_name": contact.name,
                        "verification_status": contact.verification_status,
                    }
                    _store_outcome(
                        person_record,
                        run_id=run.id,
                        organization=organization,
                        person=person,
                        score_result=person_score,
                        reason_category=import_reason_category,
                        decision_stage="import",
                        reason_details={
                            **import_reason_details,
                            "contact_priority": person.contact_priority,
                            "recommended_primary_contact": person.recommended_primary_contact,
                            "fallback_contact_used": person.fallback_contact_used,
                            "contact_selection_reason": person.contact_selection_reason,
                            "selection_reason": person.contact_selection_reason,
                            "priority_reason": reason_details,
                        },
                        final_status="imported",
                        sync_status="imported" if created_contact else "updated" if merged_contact_fields else "skipped",
                        qualification_status="qualified",
                    )
                    if created_contact:
                        run.contacts_imported += 1
                    elif merged_contact_fields:
                        run.contacts_updated += 1
                    else:
                        run.contacts_skipped += 1

                self._publish_progress(run, context)

            summary = summarize_qualification_results(
                organization_scores,
                product_name=icp.product_name,
                run_id=run.id,
                imported_count=imported_company_count,
            )
            run.qualification_evaluated_count = summary["companies_evaluated"]
            run.qualification_imported_count = summary["imported"]
            run.qualification_manual_review_count = summary["manual_review"]
            run.qualification_rejected_count = summary["rejected"]
            run.qualification_average_score = summary["average_score"]
            run.qualification_top_failure_reasons_json = json.dumps(summary["most_common_failure_reasons"], default=str)
            run.qualification_summary_json = json.dumps(summary, default=str)
            reason_breakdown = discovery_run_reasons(self.db, run.id)
            for metric in strategy_metrics.values():
                scores = metric.pop("qualification_scores", [])
                confidence_scores = metric.pop("confidence_scores", [])
                metric["average_discovery_confidence"] = round(sum(confidence_scores) / len(confidence_scores), 2) if confidence_scores else 0.0
                metric["average_qualification_score"] = round(sum(scores) / len(scores), 2) if scores else 0.0
            reason_breakdown["strategy_metrics"] = list(strategy_metrics.values())
            reason_breakdown["people_enrichment"] = {
                "attempted": enrichment_attempted,
                "succeeded": enrichment_succeeded,
                "no_match": enrichment_no_match,
            }
            reason_breakdown["organization_enrichment"] = {
                "attempted": organization_enrichment_attempted,
                "succeeded": organization_enrichment_succeeded,
                "no_match": organization_enrichment_no_match,
            }
            run.reason_breakdown_json = json.dumps(reason_breakdown, default=str)
            self.db.flush()
            self.db.commit()

            finish_run(self.db, run, context=context, status="completed")
            self.db.commit()
            return {
                "run_id": run.id,
                "product_name": icp.product_name,
                "status": run.status,
                "companies_found": run.companies_found,
                "companies_imported": run.companies_imported,
                "companies_updated": run.companies_updated,
                "companies_skipped": run.companies_skipped,
                "contacts_found": run.contacts_found,
                "contacts_imported": run.contacts_imported,
                "contacts_updated": run.contacts_updated,
                "contacts_skipped": run.contacts_skipped,
                "api_calls_used": run.api_calls_used,
                "quota_remaining": run.quota_remaining,
                "people_enrichment_attempted": enrichment_attempted,
                "people_enrichment_succeeded": enrichment_succeeded,
                "people_enrichment_no_match": enrichment_no_match,
                "organization_enrichment_attempted": organization_enrichment_attempted,
                "organization_enrichment_succeeded": organization_enrichment_succeeded,
                "organization_enrichment_no_match": organization_enrichment_no_match,
            }
        except (DiscoveryQuotaExceeded, ApolloProviderError, Exception) as exc:
            context.errors.append(str(exc))
            run.reason_breakdown_json = json.dumps(discovery_run_reasons(self.db, run.id), default=str)
            finish_run(self.db, run, context=context, status="failed")
            self.db.commit()
            return {
                "run_id": run.id,
                "product_name": icp.product_name,
                "status": run.status,
                "error": str(exc),
                "api_calls_used": run.api_calls_used,
            }
        finally:
            self.close()

    def _collect_people_for_org(
        self,
        icp: ICPProductLine,
        organization: ProviderOrganization,
        run,
        context: DiscoveryContext,
    ) -> tuple[ContactDiscoveryBatch, list]:
        records = []
        people_batch = discover_contacts_for_organization(
            self.provider_manager,
            icp,
            organization,
            max_contacts=self.settings.apollo_max_contacts_per_company,
            per_page=100,
            before_search=lambda: (self._ensure_quota(context), self._increment_calls(context)),
        )
        for person in people_batch.contacts:
            run.contacts_found += 1
            blocked_contact = find_blocked_contact_for_discovery(
                self.db,
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
                run.contacts_skipped += 1
                run.warnings_json = json.dumps(
                    (json.loads(run.warnings_json) if run.warnings_json else [])
                    + [f"Blocked do-not-contact contact: {blocked_contact.name} ({blocked_contact.id})"]
                )
                continue
            record = stage_person(self.db, run, icp, organization, person)
            records.append(record)
        return people_batch, records


def run_discovery_cycle(db: Session, *, product_names: list[str] | None = None, force: bool = False) -> list[dict]:
    engine = DiscoveryEngine(db)
    return engine.run_due(product_names=product_names, force=force)
