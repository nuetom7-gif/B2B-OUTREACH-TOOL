import os
import sys
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

from app.api import routes
from app.db import session as db_session
from app.main import app
from app.models.base import Base, Campaign, Company, CompanyProductFit, Contact, DailyLeadTarget, Mailbox, Message
from app.services.automation import list_daily_targets


class OutreachRulesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.test_sessionmaker = sessionmaker(
            bind=cls.test_engine,
            autoflush=False,
            autocommit=False,
            future=True,
        )

        db_session.engine = cls.test_engine
        db_session.SessionLocal = cls.test_sessionmaker
        routes.settings.write_api_key = "test-key"
        import app.main as main_module

        main_module.engine = cls.test_engine
        Base.metadata.create_all(bind=cls.test_engine)

    def setUp(self):
        Base.metadata.drop_all(bind=self.test_engine)
        Base.metadata.create_all(bind=self.test_engine)

    def _client(self):
        return TestClient(app)

    def _seed_contact(self, *, daily_limit: int = 1):
        session = self.test_sessionmaker()
        try:
            company = Company(name="Acme", industry="Industrial", source="Seed", notes="")
            session.add(company)
            session.flush()

            contact = Contact(
                name="Jane Doe",
                title="Procurement Manager",
                company_id=company.id,
                email="jane@example.com",
                source="Seed",
            )
            mailbox = Mailbox(name="Sales", email="sales@example.com", daily_limit=daily_limit, active=True)
            campaign = Campaign(name="Pilot", notes="", company_id=company.id)
            session.add_all([contact, mailbox, campaign])
            session.flush()
            session.commit()
            return company.id, contact.id, mailbox.id, campaign.id
        finally:
            session.close()

    def test_mailbox_daily_cap_blocks_second_send(self):
        company_id, contact_id, mailbox_id, campaign_id = self._seed_contact(daily_limit=1)

        with self._client() as client:
            headers = {"X-API-Key": "test-key"}
            draft_1 = client.post(
                "/messages/draft",
                json={
                    "contact_id": contact_id,
                    "campaign_id": campaign_id,
                    "subject": "Hello",
                    "body": "First draft",
                    "sequence_step": 0,
                },
                headers=headers,
            )
            self.assertEqual(draft_1.status_code, 200)
            message_1 = draft_1.json()["message_id"]

            send_1 = client.post(
                f"/messages/{message_1}/send",
                json={"mailbox_id": mailbox_id},
                headers=headers,
            )
            self.assertEqual(send_1.status_code, 200)

            draft_2 = client.post(
                "/messages/draft",
                json={
                    "contact_id": contact_id,
                    "campaign_id": campaign_id,
                    "subject": "Follow up",
                    "body": "Second draft",
                    "sequence_step": 1,
                },
                headers=headers,
            )
            self.assertEqual(draft_2.status_code, 200)
            message_2 = draft_2.json()["message_id"]

            send_2 = client.post(
                f"/messages/{message_2}/send",
                json={"mailbox_id": mailbox_id},
                headers=headers,
            )
            self.assertEqual(send_2.status_code, 400)
            self.assertIn("Daily send limit reached", send_2.text)

    def test_bounced_contact_cannot_get_new_draft_or_send(self):
        company_id, contact_id, mailbox_id, campaign_id = self._seed_contact(daily_limit=10)

        with self._client() as client:
            headers = {"X-API-Key": "test-key"}
            draft = client.post(
                "/messages/draft",
                json={
                    "contact_id": contact_id,
                    "campaign_id": campaign_id,
                    "subject": "Hello",
                    "body": "Initial draft",
                    "sequence_step": 0,
                },
                headers=headers,
            )
            self.assertEqual(draft.status_code, 200)
            message_id = draft.json()["message_id"]

            bounce = client.post(
                f"/messages/{message_id}/bounce",
                params={"contact_id": contact_id},
                headers=headers,
            )
            self.assertEqual(bounce.status_code, 200)

            with self.test_sessionmaker() as session:
                contact = session.get(Contact, contact_id)
                message = session.get(Message, message_id)
                self.assertTrue(contact.do_not_contact)
                self.assertEqual(message.status, "bounced")

            blocked_draft = client.post(
                "/messages/draft",
                json={
                    "contact_id": contact_id,
                    "campaign_id": campaign_id,
                    "subject": "Should not draft",
                    "body": "Blocked",
                    "sequence_step": 1,
                },
                headers=headers,
            )
            self.assertEqual(blocked_draft.status_code, 400)
            self.assertIn("do not contact", blocked_draft.text.lower())

            blocked_send = client.post(
                f"/messages/{message_id}/send",
                json={"mailbox_id": mailbox_id},
                headers=headers,
            )
            self.assertEqual(blocked_send.status_code, 400)
            self.assertIn("do not contact", blocked_send.text.lower())

    def test_contacts_csv_includes_the_linked_company_product_fits(self):
        company_id, _, _, _ = self._seed_contact()
        with self.test_sessionmaker() as session:
            session.add_all(
                [
                    CompanyProductFit(company_id=company_id, product="Industrial Vacuum Cleaning Systems"),
                    CompanyProductFit(company_id=company_id, product="Warehouse & Storage Solutions"),
                ]
            )
            session.commit()

        with self._client() as client:
            response = client.get("/contacts/export/csv")

        self.assertEqual(response.status_code, 200)
        rows = response.text.splitlines()
        self.assertIn("product_fit", rows[0])
        self.assertIn("Industrial Vacuum Cleaning Systems", rows[1])
        self.assertIn("Warehouse & Storage Solutions", rows[1])

    def test_apollo_phone_webhook_updates_the_matching_contact_idempotently(self):
        _, contact_id, _, _ = self._seed_contact()
        with self.test_sessionmaker() as session:
            contact = session.get(Contact, contact_id)
            contact.apollo_person_id = "apollo-phone-1"
            session.commit()

        original_secret = routes.settings.apollo_phone_webhook_secret
        routes.settings.apollo_phone_webhook_secret = "webhook-test-secret"
        try:
            payload = {"person": {"id": "apollo-phone-1", "phone_numbers": [{"sanitized_number": "+919876543210"}]}}
            with self._client() as client:
                response = client.post("/webhooks/apollo/phone?token=webhook-test-secret", json=payload)
                repeated = client.post("/webhooks/apollo/phone?token=webhook-test-secret", json=payload)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "updated")
            self.assertEqual(repeated.status_code, 200)
            self.assertEqual(repeated.json()["status"], "unchanged")
            with self.test_sessionmaker() as session:
                self.assertEqual(session.get(Contact, contact_id).phone, "+919876543210")
        finally:
            routes.settings.apollo_phone_webhook_secret = original_secret

    def test_apollo_phone_webhook_preserves_an_existing_phone_number(self):
        _, contact_id, _, _ = self._seed_contact()
        with self.test_sessionmaker() as session:
            contact = session.get(Contact, contact_id)
            contact.apollo_person_id = "apollo-phone-existing"
            contact.phone = "+911112223333"
            session.commit()

        original_secret = routes.settings.apollo_phone_webhook_secret
        routes.settings.apollo_phone_webhook_secret = "webhook-test-secret"
        try:
            payload = {"person": {"id": "apollo-phone-existing", "phone_numbers": [{"sanitized_number": "+919876543210"}]}}
            with self._client() as client:
                response = client.post("/webhooks/apollo/phone?token=webhook-test-secret", json=payload)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["reason"], "existing_phone_preserved")
            with self.test_sessionmaker() as session:
                self.assertEqual(session.get(Contact, contact_id).phone, "+911112223333")
        finally:
            routes.settings.apollo_phone_webhook_secret = original_secret

    def test_daily_targets_follow_enabled_configuration_without_replacing_existing_rows(self):
        with self.test_sessionmaker() as session:
            session.add(
                DailyLeadTarget(
                    product_segment="Industrial Vacuum Cleaning Systems",
                    target_leads_per_day=17,
                    companies_per_run=9,
                    contacts_per_company=3,
                    max_emails_per_batch=11,
                    active=False,
                )
            )
            session.commit()

            targets = list_daily_targets(session)
            repeated_targets = list_daily_targets(session)

            self.assertEqual(len(targets), 7)
            self.assertEqual(len(repeated_targets), 7)
            self.assertEqual({target.product_segment for target in targets}, {
                "Machine Tool Manufacturing",
                "Industrial Vacuum Cleaning Systems",
                "Warehouse & Storage Solutions",
                "Fabrication & Metal Pallets",
                "GFRP Rebar",
                "Multi-Machine Manufacturing",
                "Cool Care Manufacturing",
            })
            existing = next(target for target in repeated_targets if target.product_segment == "Industrial Vacuum Cleaning Systems")
            self.assertEqual(existing.target_leads_per_day, 17)
            self.assertEqual(existing.companies_per_run, 9)
            self.assertEqual(existing.contacts_per_company, 3)
            self.assertEqual(existing.max_emails_per_batch, 11)
            self.assertFalse(existing.active)
