import os
import json
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_bootstrap.db")
os.environ.setdefault("WRITE_API_KEY", "test-key")

from app.discovery.engine import DiscoveryEngine
from app.discovery.config_loader import load_icp_config
from app.discovery.provider import DiscoveryProvider
from app.discovery.search_builder import build_icp_search_request
from app.discovery.confidence import evaluate_discovery_confidence
from app.discovery.industry_normalization import normalize_industry
from app.discovery.diagnostics import extract_organization_fields
from app.discovery.apollo_provider import ApolloProvider
from app.discovery.search_strategy import SearchStrategy, optimize_search_strategies, plan_search_strategies
from app.discovery.types import DiscoveryCompanyCandidate, DiscoveryContactCandidate, ICPProductLine
from app.db import session as db_session
from app.api import routes
from app.main import app
from app.models.base import Base, Company, Contact, DiscoveryRun, DiscoveryStagingRecord
from app.services.discovery_merge import find_contact_for_discovery


class FakeApolloProvider(DiscoveryProvider):
    def __init__(
        self,
        organizations: list[DiscoveryCompanyCandidate],
        people_map: dict[str, list[DiscoveryContactCandidate]],
    ):
        self._organizations = organizations
        self._people_map = people_map
        self.organization_calls = 0
        self.people_calls = 0
        self.enrichment_calls = 0
        self.organization_enrichment_calls = 0

    def provider_name(self) -> str:
        return "apollo"

    def search_organizations(self, icp: ICPProductLine, *, page: int, per_page: int) -> list[DiscoveryCompanyCandidate]:
        self.organization_calls += 1
        if page > 1:
            return []
        return self._organizations[:per_page]

    def search_people(
        self,
        icp: ICPProductLine,
        organization: DiscoveryCompanyCandidate,
        *,
        page: int,
        per_page: int,
        title_filters: list[str] | None = None,
    ) -> list[DiscoveryContactCandidate]:
        self.people_calls += 1
        if page > 1:
            return []
        people = self._people_map.get(organization.source_record_id, [])
        if title_filters:
            filtered = []
            for person in people:
                title = (person.title or "").lower()
                if any(candidate.lower() in title for candidate in title_filters if candidate):
                    filtered.append(person)
            return filtered[:per_page]
        return people[:per_page]

    def close(self) -> None:
        return None

    def enrich_person(self, contact: DiscoveryContactCandidate) -> DiscoveryContactCandidate | None:
        self.enrichment_calls += 1
        return replace(contact, email="primary@example.com", email_status="verified")

    def enrich_organization(self, organization: DiscoveryCompanyCandidate) -> DiscoveryCompanyCandidate | None:
        self.organization_enrichment_calls += 1
        return replace(
            organization,
            industry=organization.industry or "Automotive Manufacturers",
            source_metadata={
                **organization.source_metadata,
                "apollo_organization_enrichment": {"response": {"organization": {"industry": "Automotive Manufacturers"}}},
            },
        )


class Phase2DiscoveryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.SessionLocal = sessionmaker(bind=cls.engine, autoflush=False, autocommit=False, future=True)
        db_session.engine = cls.engine
        db_session.SessionLocal = cls.SessionLocal
        routes.settings.write_api_key = "test-key"
        import app.main as main_module

        main_module.engine = cls.engine
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def _icp(self) -> ICPProductLine:
        return ICPProductLine(
            product_name="Industrial Vacuum Cleaning Systems",
            enabled=True,
            country=["India"],
            regions=["West India"],
            target_industries=["Automotive Manufacturers"],
            exclude_industries=[],
            company_keywords=["manufacturing", "automotive"],
            exclude_keywords=[],
            apollo_filters={"person_seniorities": ["manager", "head"]},
            employee_min=20,
            employee_max=5000,
            company_size=["medium", "large"],
            preferred_company_types=["manufacturing"],
            target_titles=["Plant Head", "Operations Manager"],
            preferred_titles=["Plant Head"],
            decision_level=["decision maker"],
            lead_score_rules={
                "industry_match": 30,
                "keyword_match": 20,
                "company_size_fit": 10,
                "decision_maker_found": 25,
                "verified_contact_present": 15,
                "import_threshold": 60,
                "manual_review_threshold": 35,
            },
            search_frequency="Daily",
            priority=1,
        )

    def _client(self):
        return TestClient(app)

    def test_staging_list_is_compact_and_detail_keeps_diagnostics(self):
        db = self.SessionLocal()
        run = DiscoveryRun(product_name="Test Product", search_frequency="Daily", status="completed")
        db.add(run)
        db.flush()
        record = DiscoveryStagingRecord(
            run_id=run.id,
            product_name="Test Product",
            provider_name="apollo",
            record_type="organization",
            company_name="Test Company",
            raw_organization_json=json.dumps({"organization": {"name": "Test Company"}}),
            qualification_input_json=json.dumps({"industry": "Machinery"}),
            qualification_result_json=json.dumps({"final_score": 42}),
            needs_manual_review=True,
            qualification_status="manual_review",
            final_status="manual_review",
            decision_stage="qualification",
            reason_category="missing_company_identifier",
            sync_status="staged",
        )
        db.add(record)
        db.commit()
        record_id = record.id
        db.close()

        client = self._client()
        list_response = client.get("/discovery/staging?limit=1")
        self.assertEqual(list_response.status_code, 200)
        payload = list_response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(len(payload["items"]), 1)
        self.assertNotIn("raw_organization", payload["items"][0])

        detail_response = client.get(f"/discovery/staging/{record_id}")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["raw_organization"]["organization"]["name"], "Test Company")

        review_response = client.get("/discovery/manual-review?limit=1")
        self.assertEqual(review_response.status_code, 200)
        self.assertEqual(review_response.json()["total"], 1)

    def test_micro_icp_profiles_build_categorized_search_intent(self):
        profiles = load_icp_config()
        profile = next(item for item in profiles if item.search_profile_name == "Laser Equipment Manufacturers")
        request = build_icp_search_request(profile, country="India", employee_min=25, employee_max=250)

        self.assertEqual(request.product_line, "Industrial Vacuum Cleaning Systems")
        self.assertEqual(request.profile_name, "Laser Equipment Manufacturers")
        self.assertEqual(request.countries, ["India"])
        self.assertEqual(request.employee_ranges, ["25,250"])
        self.assertIn("Machinery", request.exact_industries)
        self.assertIn("Mechanical or Industrial Engineering", request.exact_industries)
        self.assertIn("laser cutting", request.product_keywords)
        self.assertIn("industrial vacuum supplier", request.negative_keywords)

    def test_search_profiles_expose_backend_owned_apollo_criteria(self):
        response = self._client().get("/discovery/search-profiles")

        self.assertEqual(response.status_code, 200)
        profile = next(item for item in response.json() if item["profile_name"] == "Laser Equipment Manufacturers")
        self.assertIn("laser manufacturer", profile["company_keywords"])
        self.assertIn("CO2 laser", profile["company_keywords"])
        self.assertEqual(
            profile["apollo_industries"],
            ["Machinery", "Mechanical or Industrial Engineering", "Industrial Automation"],
        )
        self.assertEqual(profile["related_industries"], ["Electronic Manufacturing", "Semiconductors"])

    def test_government_contracting_profile_keeps_apollo_terms_together(self):
        profile = next(item for item in load_icp_config() if item.search_profile_name == "Government & Public Sector Contractors")
        provider = ApolloProvider.__new__(ApolloProvider)
        params = provider._common_org_params(profile, page=1, per_page=50)

        self.assertEqual(profile.exact_industries, ["Civil Engineering", "Construction"])
        self.assertEqual(
            params["q_organization_keyword_tags[]"],
            [
                "government contractor",
                "government contracting",
                "public sector contracting",
                "federal contractor",
                "state contractor",
                "municipal contractor",
            ],
        )

    def test_apollo_company_search_separates_keywords_from_industry_labels(self):
        profile = next(item for item in load_icp_config() if item.search_profile_name == "Laser Equipment Manufacturers")
        provider = ApolloProvider.__new__(ApolloProvider)
        params = provider._common_org_params(profile, page=1, per_page=50)

        self.assertIn("q_organization_keyword_tags[]", params)
        self.assertIn("laser manufacturer", params["q_organization_keyword_tags[]"])
        self.assertIn("laser manufacturing", params["q_organization_keyword_tags[]"])
        self.assertNotIn("Machinery", params["q_organization_keyword_tags[]"])
        self.assertNotIn("Mechanical or Industrial Engineering", params["q_organization_keyword_tags[]"])
        self.assertNotIn("q_keywords", params)

    def test_search_strategy_planner_creates_focused_industry_keyword_searches(self):
        strategies = plan_search_strategies(self._icp())

        self.assertGreaterEqual(len(strategies), 2)
        self.assertTrue(all(strategy.industry for strategy in strategies))
        self.assertTrue(all(strategy.product_keyword for strategy in strategies))
        self.assertEqual(len({strategy.name for strategy in strategies}), len(strategies))

    def test_search_strategy_planner_uses_full_industry_keyword_cross_product(self):
        icp = self._icp()
        icp.exact_industries = ["Exact Industry"]
        icp.related_industries = ["Related Industry"]
        icp.product_keywords = ["keyword one", "keyword two"]

        strategies = plan_search_strategies(icp)

        self.assertEqual(
            {(item.industry, item.product_keyword) for item in strategies},
            {
                ("Exact Industry", "keyword one"),
                ("Exact Industry", "keyword two"),
                ("Related Industry", "keyword one"),
                ("Related Industry", "keyword two"),
            },
        )

    def test_people_search_does_not_send_product_q_keywords(self):
        provider = ApolloProvider.__new__(ApolloProvider)
        provider.settings = SimpleNamespace(discovery_diagnostic_mode=False)
        provider.last_people_diagnostic = None
        captured = {}

        def fake_request(method, path, *, params=None, json=None):
            captured["method"] = method
            captured["path"] = path
            captured["params"] = params
            return {"people": []}

        provider._request = fake_request
        organization = DiscoveryCompanyCandidate(
            source_provider="apollo",
            source_record_id="org-people",
            name="People Test",
            domain="people-test.example",
        )

        provider.search_people(self._icp(), organization, page=1, per_page=10, title_filters=["Purchase Manager"])

        self.assertEqual(captured["path"], "/mixed_people/api_search")
        self.assertNotIn("q_keywords", captured["params"])

    def test_missing_company_identifier_is_explicit_manual_review(self):
        session = self.SessionLocal()
        try:
            org = DiscoveryCompanyCandidate(
                source_provider="apollo",
                source_record_id="org-no-identifier",
                name="Unmatched Fabrication Works",
                domain=None,
                industry="Automotive Manufacturers",
                employee_count=120,
                country="India",
                description="Automotive manufacturing company",
                source_metadata={"apollo_raw_record": {"name": "Unmatched Fabrication Works"}},
            )
            provider = FakeApolloProvider([org], {"org-no-identifier": []})
            engine = DiscoveryEngine(session, provider=provider)

            result = engine.run_product_line(self._icp())

            self.assertEqual(result["status"], "completed")
            staging = session.query(DiscoveryStagingRecord).filter_by(record_type="organization").one()
            self.assertEqual(staging.reason_category, "missing_company_identifier")
            self.assertEqual(staging.final_status, "manual_review")
            self.assertEqual(staging.qualification_status, "manual_review")
            self.assertTrue(staging.needs_manual_review)
            self.assertEqual(staging.sync_status, "manual_review")
            self.assertEqual(provider.people_calls, 0)
        finally:
            session.close()

    def test_organization_enrichment_populates_industry_before_confidence(self):
        session = self.SessionLocal()
        try:
            org = DiscoveryCompanyCandidate(
                source_provider="apollo",
                source_record_id="org-enrich",
                name="Enriched Automotive Works",
                domain="enriched.example",
                industry=None,
                employee_count=250,
                country="India",
                description="Automotive manufacturing company",
                source_metadata={"id": "org-enrich"},
            )
            provider = FakeApolloProvider([org], {"org-enrich": []})
            observed = {}
            original_confidence = evaluate_discovery_confidence

            def capture_confidence(icp, organization, strategy):
                observed["industry"] = organization.industry
                return original_confidence(icp, organization, strategy)

            with patch("app.discovery.engine.evaluate_discovery_confidence", side_effect=capture_confidence):
                result = DiscoveryEngine(session, provider=provider).run_product_line(self._icp())

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["organization_enrichment_attempted"], 1)
            self.assertEqual(result["organization_enrichment_succeeded"], 1)
            self.assertEqual(provider.organization_enrichment_calls, 1)
            self.assertEqual(observed["industry"], "Automotive Manufacturers")
            staging = session.query(DiscoveryStagingRecord).filter_by(record_type="organization").one()
            self.assertIn("discovery_confidence", json.loads(staging.reason_details_json))
        finally:
            session.close()

    def test_industry_normalization_reports_related_family_match(self):
        organization = DiscoveryCompanyCandidate(
            source_provider="apollo",
            source_record_id="org-family",
            name="Automation Fabrication Works",
            domain="automation.example",
            industry="Industrial Automation",
            description="Industrial automation and metal fabrication manufacturer",
            source_metadata={"apollo_raw_record": {"industries": ["Industrial Automation"], "naics_codes": ["333"]}},
        )
        result = evaluate_discovery_confidence(self._icp(), organization, plan_search_strategies(self._icp())[0])

        diagnostic = result["industry_normalization"]
        self.assertEqual(diagnostic["normalized_industry_family"], "industrial_manufacturing")
        self.assertEqual(diagnostic["matched_icp_family"], "industrial_manufacturing")
        self.assertEqual(diagnostic["match_type"], "related_family")
        self.assertEqual(diagnostic["industry_score_awarded"], 30.0)

    def test_discovery_confidence_bands_prefer_recall_without_changing_threshold(self):
        icp = self._icp()
        strategy = SearchStrategy("band", "Automotive Manufacturers", False, "manufacturing", [], [], [], [], 1)
        cases = [
            ("High Confidence", 70),
            ("Good Prospect", 45),
            ("Potential Prospect", 0),
            ("Low Relevance", -1),
        ]
        from app.discovery.confidence import confidence_band

        for expected, score in cases:
            self.assertEqual(confidence_band(score), expected)
        result = evaluate_discovery_confidence(
            icp,
            DiscoveryCompanyCandidate(
                source_provider="apollo",
                source_record_id="org-band",
                name="Adjacent Manufacturer",
                domain="adjacent.example",
                industry="Industrial Automation",
                description="Industrial automation manufacturing company",
                source_metadata={"apollo_raw_record": {"industries": ["Industrial Automation"]}},
            ),
            strategy,
        )
        self.assertEqual(result["threshold"], 30.0)
        self.assertIn(result["confidence_band"], {"Good Prospect", "Potential Prospect", "High Confidence"})

    def test_query_optimizer_normalizes_duplicates_drops_broad_keywords_and_prioritizes_tiers(self):
        icp = self._icp()
        icp.broad_industries = ["manufacturing"]
        strategies = [
            SearchStrategy("broad", "Automotive Manufacturers", False, "manufacturing", [], [], [], [], 3),
            SearchStrategy("tier2", "Automotive Manufacturers", False, "laser machine", [], [], [], [], 2),
            SearchStrategy("tier1", "Automotive Manufacturers", False, "laser cutting", [], [], [], [], 1),
            SearchStrategy("duplicate", "automotive-manufacturers", False, "LASER  CUTTING", [], [], [], [], 1),
        ]

        optimized = optimize_search_strategies(icp, strategies)

        self.assertEqual([item.product_keyword for item in optimized], ["laser cutting", "laser machine"])

    def test_description_intelligence_uses_apollo_summary_fields_and_process_signals(self):
        icp = self._icp()
        icp.product_keywords = ["laser cutting"]
        icp.process_keywords = ["precision engineering"]
        organization = DiscoveryCompanyCandidate(
            source_provider="apollo",
            source_record_id="org-description",
            name="Precision Systems",
            domain="precision-systems.example",
            industry="Automotive Manufacturers",
            description=None,
            source_metadata={"apollo_raw_record": {"headline": "Precision engineering and laser systems"}},
        )
        strategy = SearchStrategy("laser", "Automotive Manufacturers", False, "laser cutting", [], [], [], [], 1)

        result = evaluate_discovery_confidence(icp, organization, strategy)

        self.assertIn("A configured product/application signal matched the Apollo description.", result["reasons"])

    def test_apollo_mapper_recovers_nested_fields_and_records_fallback_paths(self):
        values, mapping = extract_organization_fields(
            {
                "organization": {
                    "primary_industry": "Industrial Machinery Manufacturing",
                    "estimated_num_employees": 2400,
                    "website_url": "https://nested-laser.example",
                },
                "company": {"name": "Nested Laser Systems"},
                "address": {"country": "India", "city": "Pune"},
                "organization_summary": "Laser cutting machine builder",
                "annual_revenue": 1000000,
            }
        )

        self.assertEqual(values["Company Name"], "Nested Laser Systems")
        self.assertEqual(values["Country"], "India")
        self.assertEqual(values["Employee Count"], 2400)
        self.assertEqual(values["Revenue"], 1000000)
        self.assertTrue(mapping["Company Name"]["fallback_used"])
        self.assertEqual(mapping["Company Name"]["confidence"], "medium")

    def test_qualified_discovery_imports_company_and_contact(self):
        session = self.SessionLocal()
        try:
            org = DiscoveryCompanyCandidate(
                source_provider="apollo",
                source_record_id="org-1",
                name="Acme Manufacturing",
                domain="acme.example",
                industry="Automotive Manufacturers",
                company_size="medium",
                employee_count=None,
                country="India",
                region="West India",
                description="Automotive manufacturing company",
                last_updated=datetime(2026, 7, 1, tzinfo=timezone.utc),
                source_metadata={"id": "org-1"},
            )
            person = DiscoveryContactCandidate(
                source_provider="apollo",
                source_record_id="person-1",
                organization_source_record_id="org-1",
                name="Jane Doe",
                title="Plant Head",
                email_status="verified",
                source_metadata={"id": "person-1"},
            )
            provider = FakeApolloProvider([org], {"org-1": [person]})
            engine = DiscoveryEngine(session, provider=provider)

            result = engine.run_product_line(self._icp())

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["companies_imported"], 1)
            self.assertEqual(result["contacts_imported"], 1)
            self.assertEqual(result["api_calls_used"], 9)
            self.assertEqual(result["people_enrichment_attempted"], 1)
            self.assertEqual(result["people_enrichment_succeeded"], 1)
            self.assertEqual(provider.enrichment_calls, 1)
            self.assertEqual(provider.organization_enrichment_calls, 1)

            company = session.query(Company).one()
            contact = session.query(Contact).one()
            run = session.query(DiscoveryRun).one()
            staging_records = session.query(DiscoveryStagingRecord).order_by(DiscoveryStagingRecord.record_type).all()

            self.assertEqual(company.source, "apollo_auto")
            self.assertEqual(company.source_provider, "apollo")
            self.assertEqual(company.source_record_id, "org-1")
            self.assertEqual(company.apollo_organization_id, "org-1")
            self.assertGreater(company.lead_score, 0)
            self.assertEqual(company.discovery_contacts_returned, 1)
            self.assertEqual(company.contact_status, "Contacts Found")
            self.assertEqual(contact.source, "apollo_auto")
            self.assertEqual(contact.source_provider, "apollo")
            self.assertEqual(contact.source_record_id, "person-1")
            self.assertEqual(contact.apollo_person_id, "person-1")
            self.assertEqual(contact.verification_status, "verified")
            self.assertGreater(contact.lead_score, 0)
            self.assertEqual(contact.contact_priority, "tier_2")
            self.assertTrue(contact.recommended_primary_contact)
            self.assertEqual(run.companies_found, 1)
            self.assertEqual(run.contacts_found, 1)
            self.assertEqual(len(staging_records), 2)
            self.assertEqual(staging_records[0].qualification_status, "qualified")
        finally:
            session.close()

    def test_fallback_low_priority_contacts_are_imported(self):
        session = self.SessionLocal()
        try:
            org = DiscoveryCompanyCandidate(
                source_provider="apollo",
                source_record_id="org-2",
                name="Regional Industrial Works",
                domain="regional.example",
                industry="Automotive Manufacturers",
                company_size="medium",
                employee_count=120,
                country="India",
                region="West India",
                description="Industrial manufacturing company",
                last_updated=datetime(2026, 7, 1, tzinfo=timezone.utc),
                source_metadata={"id": "org-2"},
            )
            person = DiscoveryContactCandidate(
                source_provider="apollo",
                source_record_id="person-low",
                organization_source_record_id="org-2",
                name="Ravi Kumar",
                title="Office Manager",
                email_status="unknown",
                source_metadata={"id": "person-low"},
            )
            provider = FakeApolloProvider([org], {"org-2": [person]})
            engine = DiscoveryEngine(session, provider=provider)

            result = engine.run_product_line(self._icp())

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["companies_imported"], 1)
            self.assertEqual(result["contacts_imported"], 1)
            company = session.query(Company).one()
            contact = session.query(Contact).one()
            self.assertEqual(company.contact_status, "Low Priority Contacts Found")
            self.assertEqual(company.discovery_contacts_returned, 1)
            self.assertTrue(company.fallback_contact_used)
            self.assertEqual(contact.contact_priority, "low")
            self.assertTrue(contact.recommended_primary_contact)
            self.assertEqual(provider.enrichment_calls, 1)
            self.assertEqual(result["people_enrichment_attempted"], 1)
        finally:
            session.close()

    def test_company_is_imported_even_when_apollo_returns_no_contacts(self):
        session = self.SessionLocal()
        try:
            org = DiscoveryCompanyCandidate(
                source_provider="apollo",
                source_record_id="org-empty",
                name="Precision Manufacturing Pvt Ltd",
                domain="precision.example",
                industry="Automotive Manufacturers",
                company_size="large",
                employee_count=600,
                country="India",
                region="West India",
                description="Precision component manufacturer with strong fit signals",
                last_updated=datetime(2026, 7, 1, tzinfo=timezone.utc),
                source_metadata={"id": "org-empty"},
            )
            provider = FakeApolloProvider([org], {"org-empty": []})
            engine = DiscoveryEngine(session, provider=provider)

            result = engine.run_product_line(self._icp())

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["companies_imported"], 1)
            self.assertEqual(result["contacts_imported"], 0)
            company = session.query(Company).one()
            self.assertEqual(company.discovery_contacts_returned, 0)
            self.assertEqual(company.contact_status, "No Contact Found")
            self.assertTrue(company.fallback_contact_used)
            self.assertEqual(session.query(Contact).count(), 0)
        finally:
            session.close()

    def test_discovery_stops_when_daily_call_limit_is_hit(self):
        session = self.SessionLocal()
        engine = None
        original_limit = None
        try:
            org = DiscoveryCompanyCandidate(
                source_provider="apollo",
                source_record_id="org-limit",
                name="Limit Test Manufacturing",
                domain="limit.example",
                industry="Automotive Manufacturers",
                company_size="medium",
                employee_count=120,
                country="India",
                region="West India",
                description="Manufacturing company",
                last_updated=datetime(2026, 7, 1, tzinfo=timezone.utc),
                source_metadata={"id": "org-limit"},
            )
            provider = FakeApolloProvider([org], {"org-limit": []})
            engine = DiscoveryEngine(session, provider=provider)
            original_limit = engine.settings.apollo_daily_call_limit
            engine.settings.apollo_daily_call_limit = 1

            result = engine.run_product_line(self._icp())

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["api_calls_used"], 1)
            self.assertEqual(provider.organization_calls, 1)
            self.assertEqual(provider.people_calls, 0)
            self.assertEqual(session.query(DiscoveryRun).one().status, "failed")
        finally:
            if engine is not None and original_limit is not None:
                engine.settings.apollo_daily_call_limit = original_limit
            session.close()

    def test_discovery_and_csv_import_share_contact_dedupe_rules(self):
        session = self.SessionLocal()
        try:
            company = Company(name="Shared Dedupe Ltd", industry="Industrial", source="Seed", notes="")
            session.add(company)
            session.flush()
            existing = Contact(
                name="Jane Doe",
                title="Procurement Manager",
                company_id=company.id,
                email="jane@example.com",
                source="CSV import",
            )
            session.add(existing)
            session.commit()

            with self._client() as client:
                headers = {"X-API-Key": "test-key"}
                csv_text = "name,title,company,email,source\nNew Person,Procurement Manager,Shared Dedupe Ltd,jane@example.com,CSV import\n"
                response = client.post(
                    "/contacts/import",
                    files={"file": ("contacts.csv", csv_text.encode("utf-8"), "text/csv")},
                    headers=headers,
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["skipped_duplicates"], 1)

            duplicate = find_contact_for_discovery(
                session,
                company_id=company.id,
                apollo_person_id=None,
                email="jane@example.com",
                name="New Person",
                title="Procurement Manager",
            )
            self.assertIsNotNone(duplicate)
            self.assertEqual(duplicate.id, existing.id)
            self.assertEqual(session.query(Contact).count(), 1)
        finally:
            session.close()

    def test_do_not_contact_contact_is_blocked_before_staging_and_import(self):
        session = self.SessionLocal()
        try:
            company = Company(
                name="Acme Manufacturing",
                industry="Automotive Manufacturers",
                source="Manual",
                notes="",
                apollo_organization_id="org-dnc",
            )
            session.add(company)
            session.flush()
            contact = Contact(
                name="Jane Doe",
                title="Plant Head",
                company_id=company.id,
                email="jane.dnc@example.com",
                source="Manual",
                do_not_contact=True,
                apollo_person_id="person-dnc",
            )
            session.add(contact)
            session.commit()

            org = DiscoveryCompanyCandidate(
                source_provider="apollo",
                source_record_id="org-dnc",
                name="Acme Manufacturing",
                domain="acme.example",
                industry="Automotive Manufacturers",
                company_size="medium",
                employee_count=150,
                country="India",
                region="West India",
                description="Automotive manufacturing company",
                last_updated=datetime(2026, 7, 1, tzinfo=timezone.utc),
                source_metadata={"id": "org-dnc"},
            )
            person = DiscoveryContactCandidate(
                source_provider="apollo",
                source_record_id="person-dnc",
                organization_source_record_id="org-dnc",
                name="Jane Doe",
                title="Plant Head",
                email="jane.dnc@example.com",
                email_status="verified",
                source_metadata={"id": "person-dnc"},
            )
            provider = FakeApolloProvider([org], {"org-dnc": [person]})
            engine = DiscoveryEngine(session, provider=provider)

            result = engine.run_product_line(self._icp())

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["contacts_imported"], 0)
            self.assertEqual(result["contacts_updated"], 0)
            self.assertEqual(session.query(Contact).count(), 1)
            self.assertEqual(session.query(DiscoveryStagingRecord).filter_by(record_type="person").count(), 0)
            self.assertEqual(provider.people_calls, 5)
        finally:
            session.close()
