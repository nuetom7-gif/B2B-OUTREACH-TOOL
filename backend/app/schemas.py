from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProductFitCreate(BaseModel):
    product: str


class CompanyCreate(BaseModel):
    name: str
    industry: str
    source: str
    notes: str = ""
    product_fits: list[str] = Field(default_factory=list)


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    industry: str
    source: str
    source_provider: str | None = None
    source_record_id: str | None = None
    notes: str
    product_fits: list[str] = Field(default_factory=list)
    contact_count: int = 0
    apollo_organization_id: str | None = None
    apollo_last_updated: datetime | None = None
    last_sync: datetime | None = None
    sync_status: str = "pending"
    needs_manual_review: bool = False
    owner_id: int | None = None
    assignment_status: str = "unassigned"
    assigned_at: datetime | None = None
    assignment_source: str | None = None
    lead_score: int = 0


class ContactCreate(BaseModel):
    name: str
    title: str
    company_id: int
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    source: str


class ContactRead(BaseModel):
    id: int
    name: str
    title: str
    company_id: int
    company_name: str
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    do_not_contact: bool
    added_at: datetime
    source: str
    source_provider: str | None = None
    source_record_id: str | None = None
    latest_message_subject: str | None = None
    latest_message_status: str | None = None
    apollo_person_id: str | None = None
    verification_status: str = "unknown"
    last_sync: datetime | None = None
    lead_score: int = 0


class CampaignCreate(BaseModel):
    name: str
    notes: str = ""
    company_id: int | None = None


class CampaignRead(BaseModel):
    id: int
    name: str
    notes: str
    company_name: str | None = None
    message_count: int = 0


class MailboxCreate(BaseModel):
    name: str
    email: str
    daily_limit: int = 30
    active: bool = True


class MailboxRead(BaseModel):
    id: int
    name: str
    email: str
    daily_limit: int
    active: bool
    sent_today: int = 0


class MessageDraftCreate(BaseModel):
    contact_id: int
    subject: str
    body: str
    sequence_step: int = 0
    campaign_id: int | None = None


class MessageSendCreate(BaseModel):
    mailbox_id: int


class ReplyCreate(BaseModel):
    message_id: int
    contact_id: int
    body: str
    outcome: str


class FollowUpCreate(BaseModel):
    message_id: int
    contact_id: int
    follow_up_at: datetime


class DashboardRead(BaseModel):
    total_contacts: int
    messages_sent_this_month: int
    reply_rate: float
    active_mailboxes: int
    product_breakdown: list[dict[str, Any]]
    recent_messages: list[dict[str, Any]]


class DiscoveryRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    search_frequency: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    companies_found: int
    companies_imported: int
    companies_updated: int
    companies_skipped: int
    contacts_found: int
    contacts_imported: int
    contacts_updated: int
    contacts_skipped: int
    api_calls_used: int
    quota_remaining: int | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DiscoveryStagingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    product_name: str
    provider_name: str
    record_type: str
    apollo_organization_id: str | None = None
    apollo_person_id: str | None = None
    company_name: str | None = None
    company_domain: str | None = None
    industry: str | None = None
    country: str | None = None
    region: str | None = None
    employee_count: int | None = None
    company_size: str | None = None
    person_name: str | None = None
    person_title: str | None = None
    person_email: str | None = None
    person_phone: str | None = None
    person_linkedin_url: str | None = None
    person_seniority: str | None = None
    qualification_status: str
    score: int
    confidence: str
    needs_manual_review: bool
    sync_status: str
    error_message: str | None = None
    warning_message: str | None = None
    crm_company_id: int | None = None
    crm_contact_id: int | None = None
    apollo_last_updated: datetime | None = None
    last_sync: datetime | None = None


class DiscoveryRunRequest(BaseModel):
    product_names: list[str] | None = None
    force: bool = False
