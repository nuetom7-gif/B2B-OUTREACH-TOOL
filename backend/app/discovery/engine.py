from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.discovery.apollo_provider import ApolloProviderError
from app.discovery.config_loader import load_icp_config
from app.discovery.provider import DiscoveryProvider
from app.discovery.provider_manager import DiscoveryProviderManager, create_default_provider_manager
from app.discovery.qualification import score_organization, score_person
from app.discovery.repository import (
    create_run,
    due_for_frequency,
    finish_run,
    latest_run_for_product,
    now_utc,
    stage_organization,
    stage_person,
    todays_api_calls_used,
)
from app.discovery.types import DiscoveryContext, ICPProductLine, ProviderOrganization, ProviderPerson
from app.services.discovery_merge import (
    find_blocked_contact_for_discovery,
    upsert_company_from_discovery,
    upsert_contact_from_discovery,
)


class DiscoveryQuotaExceeded(RuntimeError):
    pass


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

    def run_product_line(self, icp: ICPProductLine) -> dict:
        run = create_run(self.db, icp)
        context = DiscoveryContext(product_line=icp, run_id=run.id)
        try:
            company_records: list[tuple[ProviderOrganization, object, list[ProviderPerson], list[object]]] = []
            org_page = 1
            per_page = 100
            max_companies = self.settings.apollo_max_companies_per_run
            while len(company_records) < max_companies:
                self._ensure_quota(context)
                organizations = self.provider_manager.search_organizations(icp, page=org_page, per_page=per_page)
                self._increment_calls(context)
                if not organizations:
                    break
                run.companies_found += len(organizations)
                for organization in organizations:
                    if len(company_records) >= max_companies:
                        break
                    org_record = stage_organization(self.db, run, icp, organization)
                    people, person_records = self._collect_people_for_org(icp, organization, run, context)
                    company_records.append((organization, org_record, people, person_records))
                if len(organizations) < per_page:
                    break
                org_page += 1

            for organization, org_record, people, person_records in company_records:
                org_score = score_organization(icp, organization, people)
                org_record.score = int(org_score.score)
                org_record.needs_manual_review = org_score.needs_manual_review
                org_record.confidence = "high" if org_score.status == "qualified" else "medium" if org_score.status == "manual_review" else "low"
                org_record.qualification_status = org_score.status
                org_record.sync_status = "manual_review" if org_score.status == "manual_review" else "rejected"
                org_record.warning_message = "; ".join(org_score.reasons) if org_score.reasons else None
                if org_score.status != "qualified":
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
                    "needs_manual_review": False,
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
                company.needs_manual_review = False
                org_record.crm_company_id = company.id
                org_record.last_sync = now_utc()
                org_record.sync_status = "imported" if created else "updated" if merged_fields else "skipped"
                org_record.qualification_status = "qualified"
                if created:
                    run.companies_imported += 1
                elif merged_fields:
                    run.companies_updated += 1
                else:
                    run.companies_skipped += 1

                for person, person_record in zip(people, person_records):
                    person_score = score_person(icp, person)
                    contact_score = int(org_score.score + person_score.score)
                    person_record.score = contact_score
                    person_record.needs_manual_review = person_score.needs_manual_review or contact_score < int(
                        icp.lead_score_rules.get("import_threshold", 60)
                    )
                    person_record.confidence = "high" if contact_score >= int(icp.lead_score_rules.get("import_threshold", 60)) else "medium" if contact_score >= int(icp.lead_score_rules.get("manual_review_threshold", 35)) else "low"
                    person_record.qualification_status = (
                        "qualified"
                        if contact_score >= int(icp.lead_score_rules.get("import_threshold", 60)) and person_score.matched_decision_maker
                        else "manual_review"
                        if person_record.needs_manual_review
                        else "rejected"
                    )
                    person_record.sync_status = "manual_review" if person_record.qualification_status == "manual_review" else "rejected"
                    person_record.warning_message = "; ".join(person_score.reasons) if person_score.reasons else None
                    if person_record.qualification_status != "qualified":
                        run.contacts_skipped += 1
                        continue
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
                        person_record.qualification_status = "rejected"
                        person_record.sync_status = "rejected"
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
                    person_record.crm_contact_id = contact.id
                    person_record.last_sync = now_utc()
                    person_record.sync_status = "imported" if created_contact else "updated" if merged_contact_fields else "skipped"
                    if created_contact:
                        run.contacts_imported += 1
                    elif merged_contact_fields:
                        run.contacts_updated += 1
                    else:
                        run.contacts_skipped += 1

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
            }
        except (DiscoveryQuotaExceeded, ApolloProviderError, Exception) as exc:
            context.errors.append(str(exc))
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
    ) -> tuple[list[ProviderPerson], list]:
        people: list[ProviderPerson] = []
        records = []
        page = 1
        per_page = 100
        while len(people) < self.settings.apollo_max_contacts_per_company:
            self._ensure_quota(context)
            results = self.provider_manager.search_people(icp, organization, page=page, per_page=per_page)
            self._increment_calls(context)
            if not results:
                break
            for person in results:
                if len(people) >= self.settings.apollo_max_contacts_per_company:
                    break
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
                        + [f"Blocked do-not-contact contact before staging: {blocked_contact.name} ({blocked_contact.id})"]
                    )
                    continue
                record = stage_person(self.db, run, icp, organization, person)
                records.append(record)
                people.append(person)
                run.contacts_found += 1
            if len(results) < per_page:
                break
            page += 1
        return people, records


def run_discovery_cycle(db: Session, *, product_names: list[str] | None = None, force: bool = False) -> list[dict]:
    engine = DiscoveryEngine(db)
    return engine.run_due(product_names=product_names, force=force)
