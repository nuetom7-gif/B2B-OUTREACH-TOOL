import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest import TestCase

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
from app.discovery.provider import DiscoveryProvider
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
    ) -> list[DiscoveryContactCandidate]:
        self.people_calls += 1
        if page > 1:
            return []
        return self._people_map.get(organization.source_record_id, [])[:per_page]

    def close(self) -> None:
        return None


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
            self.assertEqual(result["api_calls_used"], 2)

            company = session.query(Company).one()
            contact = session.query(Contact).one()
            run = session.query(DiscoveryRun).one()
            staging_records = session.query(DiscoveryStagingRecord).order_by(DiscoveryStagingRecord.record_type).all()

            self.assertEqual(company.source, "apollo_auto")
            self.assertEqual(company.source_provider, "apollo")
            self.assertEqual(company.source_record_id, "org-1")
            self.assertEqual(company.apollo_organization_id, "org-1")
            self.assertGreater(company.lead_score, 0)
            self.assertEqual(contact.source, "apollo_auto")
            self.assertEqual(contact.source_provider, "apollo")
            self.assertEqual(contact.source_record_id, "person-1")
            self.assertEqual(contact.apollo_person_id, "person-1")
            self.assertEqual(contact.verification_status, "verified")
            self.assertGreater(contact.lead_score, 0)
            self.assertEqual(run.companies_found, 1)
            self.assertEqual(run.contacts_found, 1)
            self.assertEqual(len(staging_records), 2)
            self.assertEqual(staging_records[0].qualification_status, "qualified")
        finally:
            session.close()

    def test_low_confidence_discovery_stays_in_manual_review(self):
        session = self.SessionLocal()
        try:
            org = DiscoveryCompanyCandidate(
                source_provider="apollo",
                source_record_id="org-2",
                name="Regional Industrial Works",
                domain="regional.example",
                industry="Automotive Manufacturers",
                company_size=None,
                employee_count=None,
                country="India",
                region="West India",
                description="Industrial manufacturing company",
                last_updated=datetime(2026, 7, 1, tzinfo=timezone.utc),
                source_metadata={"id": "org-2"},
            )
            provider = FakeApolloProvider([org], {"org-2": []})
            engine = DiscoveryEngine(session, provider=provider)

            result = engine.run_product_line(self._icp())

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["companies_imported"], 0)
            self.assertEqual(result["contacts_imported"], 0)
            self.assertEqual(result["companies_skipped"], 1)

            self.assertEqual(session.query(Company).count(), 0)
            self.assertEqual(session.query(Contact).count(), 0)
            staging = session.query(DiscoveryStagingRecord).filter_by(record_type="organization").one()
            self.assertTrue(staging.needs_manual_review)
            self.assertEqual(staging.qualification_status, "manual_review")
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
            self.assertEqual(provider.people_calls, 1)
        finally:
            session.close()
