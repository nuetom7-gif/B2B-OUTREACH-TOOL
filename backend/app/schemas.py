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


class ContactUpdate(BaseModel):
    name: str
    title: str
    company_id: int | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    do_not_contact: bool = False


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


class DashboardStatsRead(BaseModel):
    today_leads: dict[str, dict[str, int]]
    today_emails_sent: int
    today_replies: int
    reply_rate: float
    bounce_rate: float
    apollo_credits_remaining: int
    pending_drafts: int
    pending_reviews: int
    do_not_contact_count: int
    per_product_stats: list[dict[str, Any]]
    daily_leads: list[dict[str, Any]]
    daily_emails: list[dict[str, Any]]
    daily_replies: list[dict[str, Any]]
    funnel: dict[str, int]
    recent_activity: list[dict[str, Any]]
    active_mailboxes: int
    total_contacts: int


class DiscoveryJobCreate(BaseModel):
    product_segment: str
    industry: str
    country: str
    state: str | None = None
    keywords: str = ""
    company_limit: int = 30
    contacts_per_company: int = 2
    max_leads: int = 60


class DiscoveryJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_segment: str
    industry: str
    country: str
    state: str | None = None
    keywords: str = ""
    company_limit: int
    contacts_per_company: int
    max_leads: int
    status: str
    current_step: str
    progress_percent: int
    companies_found: int
    companies_processed: int
    contacts_discovered: int
    qualified_leads: int
    imported_leads: int
    skipped_leads: int
    failed_leads: int
    api_calls_used: int
    quota_remaining: int | None = None
    request_json: str
    result_json: str
    error_message: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancel_requested: bool = False


class DiscoveryJobLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    level: str
    message: str
    metadata_json: str
    created_at: datetime


class DailyLeadTargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_segment: str
    target_leads_per_day: int = 60
    companies_per_run: int = 30
    contacts_per_company: int = 2
    max_emails_per_batch: int = 60
    active: bool = True
    default_campaign_id: int | None = None
    default_mailbox_id: int | None = None
    today_leads: int = 0


class DailyLeadTargetUpdate(BaseModel):
    product_segment: str
    target_leads_per_day: int = 60
    companies_per_run: int = 30
    contacts_per_company: int = 2
    max_emails_per_batch: int = 60
    active: bool = True
    default_campaign_id: int | None = None
    default_mailbox_id: int | None = None


class WorkspaceSettingRead(BaseModel):
    key: str
    value: str


class WorkspaceSettingUpdate(BaseModel):
    key: str
    value: str


class DraftGenerateRequest(BaseModel):
    lead_id: int
    campaign_id: int | None = None
    product_segment: str
    tone: str = "professional"
    length: str = "short"


class DraftUpdateRequest(BaseModel):
    subject: str
    body: str
    campaign_id: int | None = None
    sequence_step: int = 0


class DraftRead(BaseModel):
    id: int
    contact_id: int
    contact_name: str
    company_name: str
    campaign_id: int | None = None
    campaign_name: str | None = None
    subject: str
    body: str
    status: str
    sequence_step: int
    updated_at: datetime


class BulkSendRequest(BaseModel):
    contact_ids: list[int] = Field(default_factory=list)
    campaign_id: int | None = None
    mailbox_id: int
    subject: str
    body: str
    product_segment: str | None = None
    limit: int | None = None


class BulkSendResult(BaseModel):
    sent: int
    failed: int
    skipped: int
    errors: list[str] = Field(default_factory=list)


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
    qualification_summary: dict[str, Any] = Field(default_factory=dict)
    qualification_top_failure_reasons: list[dict[str, Any]] = Field(default_factory=list)
    reason_breakdown: dict[str, Any] = Field(default_factory=dict)
    qualification_average_score: float = 0.0
    qualification_evaluated_count: int = 0
    qualification_imported_count: int = 0
    qualification_manual_review_count: int = 0
    qualification_rejected_count: int = 0


class DiscoveryRunReasonsRead(BaseModel):
    run_id: int
    product_name: str
    status: str
    total_candidates_found: int
    imported_count: int
    reason_counts: list[dict[str, Any]] = Field(default_factory=list)
    success_counts: list[dict[str, Any]] = Field(default_factory=list)
    final_status_counts: list[dict[str, Any]] = Field(default_factory=list)


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
    final_status: str
    decision_stage: str
    reason_category: str
    reason_details: dict[str, Any] = Field(default_factory=dict)
    score: int
    qualification_threshold: int | None = None
    manual_review_threshold: int | None = None
    qualification_evaluated_at: datetime | None = None
    qualification_result: dict[str, Any] = Field(default_factory=dict)
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
    product_segment: str | None = None
    industry: str | None = None
    country: str | None = None
    state: str | None = None
    keywords: str | None = None
    company_limit: int | None = None
    contacts_per_company: int | None = None
    max_leads: int | None = None
