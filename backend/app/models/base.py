from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class CompanyProductFit(Base):
    __tablename__ = "company_product_fits"
    __table_args__ = (UniqueConstraint("company_id", "product", name="uq_company_product_fit"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    product: Mapped[str] = mapped_column(String(64), nullable=False)

    company = relationship("Company", back_populates="product_fits")


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    apollo_organization_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    apollo_last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    needs_manual_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    discovery_contacts_returned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contact_status: Mapped[str] = mapped_column(String(64), default="No Contact Found", nullable=False)
    fallback_contact_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assignment_status: Mapped[str] = mapped_column(String(32), default="unassigned", nullable=False)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assignment_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lead_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="company")
    product_fits = relationship("CompanyProductFit", back_populates="company", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="company")


class Contact(Base, TimestampMixin):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    do_not_contact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    apollo_person_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lead_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contact_priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recommended_primary_contact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fallback_contact_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contact_selection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    discovery_profiles_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    company = relationship("Company", back_populates="contacts")
    messages = relationship("Message", back_populates="contact", cascade="all, delete-orphan")
    replies = relationship("Reply", back_populates="contact", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="contact")


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)

    company = relationship("Company", back_populates="campaigns")
    messages = relationship("Message", back_populates="campaign")
    audit_events = relationship("AuditEvent", back_populates="campaign")


class Mailbox(Base, TimestampMixin):
    __tablename__ = "mailboxes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    daily_limit: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    messages = relationship("Message", back_populates="mailbox")
    audit_events = relationship("AuditEvent", back_populates="mailbox")


class WorkspaceSetting(Base, TimestampMixin):
    __tablename__ = "workspace_settings"
    __table_args__ = (UniqueConstraint("key", name="uq_workspace_settings_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(Text, default="", nullable=False)


class DailyLeadTarget(Base, TimestampMixin):
    __tablename__ = "daily_lead_targets"
    __table_args__ = (UniqueConstraint("product_segment", name="uq_daily_lead_targets_product_segment"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_segment: Mapped[str] = mapped_column(String(255), nullable=False)
    target_leads_per_day: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    companies_per_run: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    contacts_per_company: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_emails_per_batch: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    default_mailbox_id: Mapped[int | None] = mapped_column(ForeignKey("mailboxes.id", ondelete="SET NULL"), nullable=True)

    default_campaign = relationship("Campaign")
    default_mailbox = relationship("Mailbox")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    mailbox_id: Mapped[int | None] = mapped_column(ForeignKey("mailboxes.id", ondelete="SET NULL"), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sequence_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    contact = relationship("Contact", back_populates="messages")
    campaign = relationship("Campaign", back_populates="messages")
    mailbox = relationship("Mailbox", back_populates="messages")
    replies = relationship("Reply", back_populates="message", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="message")


class Reply(Base):
    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    outcome: Mapped[str] = mapped_column(String(255), nullable=False)

    message = relationship("Message", back_populates="replies")
    contact = relationship("Contact", back_populates="replies")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=True)
    mailbox_id: Mapped[int | None] = mapped_column(ForeignKey("mailboxes.id", ondelete="CASCADE"), nullable=True)

    company = relationship("Company", back_populates="audit_events")
    contact = relationship("Contact", back_populates="audit_events")
    campaign = relationship("Campaign", back_populates="audit_events")
    message = relationship("Message", back_populates="audit_events")
    mailbox = relationship("Mailbox", back_populates="audit_events")


class DiscoveryRun(Base, TimestampMixin):
    __tablename__ = "discovery_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    search_frequency: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    companies_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    companies_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    companies_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    companies_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacts_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacts_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacts_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacts_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    api_calls_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quota_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    errors_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    warnings_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    qualification_summary_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    qualification_top_failure_reasons_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    reason_breakdown_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    qualification_average_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    qualification_evaluated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qualification_imported_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qualification_manual_review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qualification_rejected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    staging_records = relationship("DiscoveryStagingRecord", back_populates="run", cascade="all, delete-orphan")


class DiscoveryStagingRecord(Base, TimestampMixin):
    __tablename__ = "discovery_staging_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("discovery_runs.id", ondelete="CASCADE"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    record_type: Mapped[str] = mapped_column(String(32), nullable=False)
    apollo_organization_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    apollo_person_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(64), nullable=True)
    person_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    person_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    person_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    person_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    person_linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    person_seniority: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    raw_organization_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    organization_mapping_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    people_request_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    raw_people_response_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    normalized_company_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    normalized_contacts_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    qualification_input_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    qualification_status: Mapped[str] = mapped_column(String(32), default="staged", nullable=False)
    final_status: Mapped[str] = mapped_column(String(32), default="staged", nullable=False)
    decision_stage: Mapped[str] = mapped_column(String(64), default="staged", nullable=False)
    reason_category: Mapped[str] = mapped_column(String(64), default="staged", nullable=False)
    reason_details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qualification_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manual_review_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qualification_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    qualification_result_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    confidence: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    needs_manual_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sync_status: Mapped[str] = mapped_column(String(32), default="staged", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    warning_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    crm_company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    crm_contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    apollo_last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    run = relationship("DiscoveryRun", back_populates="staging_records")


class DiscoveryJob(Base, TimestampMixin):
    __tablename__ = "discovery_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_segment: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    keywords: Mapped[str] = mapped_column(Text, default="", nullable=False)
    company_limit: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    contacts_per_company: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_leads: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    current_step: Mapped[str] = mapped_column(String(255), default="queued", nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    companies_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    companies_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacts_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qualified_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    api_calls_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quota_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    result_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    logs = relationship("DiscoveryJobLog", back_populates="job", cascade="all, delete-orphan")


class DiscoveryJobLog(Base):
    __tablename__ = "discovery_job_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("discovery_jobs.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[str] = mapped_column(String(32), default="info", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    job = relationship("DiscoveryJob", back_populates="logs")
