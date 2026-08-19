from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models.base import Campaign, Company, CompanyProductFit, Contact, Mailbox, Message, Reply
from app.schemas import (
    BulkSendRequest,
    CampaignCreate,
    CampaignRead,
    CompanyCreate,
    CompanyRead,
    DailyLeadTargetRead,
    DailyLeadTargetUpdate,
    ContactCreate,
    ContactRead,
    ContactUpdate,
    DashboardRead,
    DashboardStatsRead,
    DraftGenerateRequest,
    DraftRead,
    DraftUpdateRequest,
    FollowUpCreate,
    MailboxCreate,
    MailboxRead,
    MessageDraftCreate,
    MessageSendCreate,
    ReplyCreate,
    WorkspaceSettingRead,
    WorkspaceSettingUpdate,
    WorkspaceProfileRead,
)
from app.services.csv_service import pick_field, read_csv_upload, split_list
from app.services.discovery_merge import contact_discovery_profiles, find_contact_for_discovery
from app.services.automation import (
    create_draft,
    dashboard_stats,
    daily_target_snapshot,
    list_drafts,
    settings_snapshot,
    send_bulk_messages,
    upsert_daily_targets,
    upsert_workspace_settings,
    update_draft,
)
from app.services.outreach import (
    add_audit,
    company_contact_count,
    company_product_fits,
    daily_sent_count,
    ensure_opt_out_line,
    product_breakdown,
    recent_messages,
)

router = APIRouter()
settings = get_settings()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_company_or_404(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def get_contact_or_404(db: Session, contact_id: int) -> Contact:
    contact = db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


def _apollo_phone_from_webhook(payload: dict) -> tuple[str | None, str | None]:
    """Accept Apollo's native and waterfall phone payload shapes."""
    person = payload.get("person") or payload.get("contact") or payload.get("data") or payload
    if not isinstance(person, dict):
        return None, None
    person_id = person.get("person_id") or person.get("id") or person.get("apollo_person_id")
    phones = person.get("phone_numbers") or person.get("phones") or []
    if isinstance(phones, dict):
        phones = [phones]
    if isinstance(phones, list):
        for phone in phones:
            if isinstance(phone, dict):
                value = phone.get("sanitized_number") or phone.get("raw_number") or phone.get("number") or phone.get("phone")
            else:
                value = phone
            if str(value or "").strip():
                return str(person_id or "").strip() or None, str(value).strip()
    for key in ("phone", "mobile_phone", "direct_phone", "raw_number", "sanitized_number"):
        value = person.get(key)
        if str(value or "").strip():
            return str(person_id or "").strip() or None, str(value).strip()
    return str(person_id or "").strip() or None, None


@router.post("/webhooks/apollo/phone")
def receive_apollo_phone_webhook(
    payload: dict,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if not settings.apollo_phone_webhook_secret:
        raise HTTPException(status_code=503, detail="Apollo phone webhook is not configured")
    if token != settings.apollo_phone_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    person_id, phone = _apollo_phone_from_webhook(payload)
    if not person_id:
        raise HTTPException(status_code=400, detail="Apollo phone webhook did not include a person identifier")
    if not phone:
        return {"status": "ignored", "reason": "no_phone_returned", "person_id": person_id}

    contact = db.execute(select(Contact).where(Contact.apollo_person_id == person_id)).scalar_one_or_none()
    if contact is None:
        return {"status": "ignored", "reason": "contact_not_found", "person_id": person_id}

    if contact.phone == phone:
        return {"status": "unchanged", "contact_id": contact.id}

    # Apollo enrichment may fill an absent number, but must never replace a
    # number already entered through the CRM, CSV import, or a prior source.
    if (contact.phone or "").strip():
        return {"status": "unchanged", "reason": "existing_phone_preserved", "contact_id": contact.id}

    contact.phone = phone
    contact.last_sync = now_utc()
    add_audit(
        db,
        entity_type="contact",
        entity_id=str(contact.id),
        action="apollo_phone_enriched",
        reason="Apollo phone enrichment webhook received",
        metadata={"apollo_person_id": person_id},
        contact_id=contact.id,
        company_id=contact.company_id,
    )
    db.commit()
    return {"status": "updated", "contact_id": contact.id}


def get_message_or_404(db: Session, message_id: int) -> Message:
    message = db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


def company_to_read(company: Company, contact_count: int) -> CompanyRead:
    return CompanyRead(
        id=company.id,
        name=company.name,
        industry=company.industry,
        source=company.source,
        source_provider=company.source_provider,
        source_record_id=company.source_record_id,
        notes=company.notes,
        product_fits=company_product_fits(company),
        contact_count=contact_count,
        apollo_organization_id=company.apollo_organization_id,
        apollo_last_updated=company.apollo_last_updated,
        last_sync=company.last_sync,
        sync_status=company.sync_status,
        needs_manual_review=company.needs_manual_review,
        owner_id=company.owner_id,
        assignment_status=company.assignment_status,
        assigned_at=company.assigned_at,
        assignment_source=company.assignment_source,
        lead_score=company.lead_score,
        discovery_contacts_returned=company.discovery_contacts_returned,
        contact_status=company.contact_status,
        fallback_contact_used=company.fallback_contact_used,
    )


def contact_to_read(contact: Contact, latest_message: Message | None = None) -> ContactRead:
    return ContactRead(
        id=contact.id,
        name=contact.name,
        title=contact.title,
        company_id=contact.company_id,
        company_name=contact.company.name,
        email=contact.email,
        phone=contact.phone,
        linkedin_url=contact.linkedin_url,
        do_not_contact=contact.do_not_contact,
        added_at=contact.added_at,
        source=contact.source,
        source_provider=contact.source_provider,
        source_record_id=contact.source_record_id,
        latest_message_subject=latest_message.subject if latest_message else None,
        latest_message_status=latest_message.status if latest_message else None,
        apollo_person_id=contact.apollo_person_id,
        verification_status=contact.verification_status,
        last_sync=contact.last_sync,
        lead_score=contact.lead_score,
        contact_priority=contact.contact_priority,
        recommended_primary_contact=contact.recommended_primary_contact,
        fallback_contact_used=contact.fallback_contact_used,
        contact_selection_reason=contact.contact_selection_reason,
        discovery_profiles=contact_discovery_profiles(contact),
    )


def require_write_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    expected = settings.write_api_key.strip()
    if not expected:
        raise HTTPException(status_code=500, detail="WRITE_API_KEY is not configured")
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/workspace/profile", response_model=WorkspaceProfileRead)
def workspace_profile():
    return WorkspaceProfileRead(
        company_name=settings.workspace_company_name,
        user_name=settings.workspace_user_name,
        user_role=settings.workspace_user_role,
    )


@router.get("/dashboard", response_model=DashboardRead)
def dashboard(db: Session = Depends(get_db)):
    total_contacts = db.scalar(select(func.count(Contact.id))) or 0
    sent_this_month = db.scalar(
        select(func.count(Message.id)).where(
            Message.status == "sent",
            Message.sent_at >= now_utc().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        )
    ) or 0
    replies = db.scalar(select(func.count(Reply.id))) or 0
    active_mailboxes = db.scalar(select(func.count(Mailbox.id)).where(Mailbox.active.is_(True))) or 0
    reply_rate = 0.0 if sent_this_month == 0 else replies / sent_this_month
    return DashboardRead(
        total_contacts=total_contacts,
        messages_sent_this_month=sent_this_month,
        reply_rate=reply_rate,
        active_mailboxes=active_mailboxes,
        product_breakdown=product_breakdown(db),
        recent_messages=recent_messages(db),
    )


@router.get("/dashboard/stats", response_model=DashboardStatsRead)
def dashboard_stats_endpoint(db: Session = Depends(get_db)):
    return dashboard_stats(db)


@router.get("/companies", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)):
    companies = db.execute(select(Company).order_by(Company.created_at.desc())).scalars().all()
    return [company_to_read(company, company_contact_count(db, company.id)) for company in companies]


@router.get("/companies/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = get_company_or_404(db, company_id)
    return company_to_read(company, company_contact_count(db, company.id))


@router.post("/companies", response_model=CompanyRead)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    company = Company(name=payload.name, industry=payload.industry, source=payload.source, notes=payload.notes)
    db.add(company)
    db.flush()
    for product in payload.product_fits:
        db.add(CompanyProductFit(company_id=company.id, product=product))
    add_audit(
        db,
        entity_type="company",
        entity_id=str(company.id),
        action="created",
        reason=f"Company added manually from {payload.source}.",
        metadata={"name": payload.name, "industry": payload.industry, "fits": payload.product_fits},
        company_id=company.id,
    )
    db.commit()
    db.refresh(company)
    return company_to_read(company, 0)


@router.post("/companies/import")
async def import_companies(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    frame = read_csv_upload(await file.read())
    created = 0
    reused = 0
    product_fits_added = 0
    for row in frame.fillna("").to_dict(orient="records"):
        name = pick_field(row, ["company", "company name", "name"])
        industry = pick_field(row, ["industry", "sector"])
        if not name or not industry:
            continue
        source = pick_field(row, ["source", "found via", "how found"]) or "CSV import"
        notes = pick_field(row, ["notes", "comment", "commentary"])
        fits_raw = pick_field(row, ["product_fit", "product fit", "productfits", "fit"])
        company = db.execute(select(Company).where(Company.name == name)).scalars().first()
        if not company:
            company = Company(name=name, industry=industry, source=source, notes=notes)
            db.add(company)
            db.flush()
            add_audit(
                db,
                entity_type="company",
                entity_id=str(company.id),
                action="imported",
                reason="Imported from CSV.",
                metadata={"source": source, "row": row},
                company_id=company.id,
            )
            created += 1
        else:
            reused += 1

        existing_products = {fit.product for fit in company.product_fits}
        for product in split_list(fits_raw):
            if product not in existing_products:
                db.add(CompanyProductFit(company_id=company.id, product=product))
                existing_products.add(product)
                product_fits_added += 1
    db.commit()
    return {"created": created, "reused": reused, "product_fits_added": product_fits_added}


@router.get("/companies/export")
def export_companies(db: Session = Depends(get_db)):
    companies = list_companies(db)
    df = pd.DataFrame([company.model_dump() for company in companies])
    return pd.DataFrame.to_csv(df, index=False)


@router.get("/contacts", response_model=list[ContactRead])
def list_contacts(db: Session = Depends(get_db)):
    contacts = db.execute(select(Contact).order_by(Contact.added_at.desc())).scalars().all()
    payload: list[ContactRead] = []
    for contact in contacts:
        latest_message = (
            db.execute(
                select(Message).where(Message.contact_id == contact.id).order_by(Message.created_at.desc()).limit(1)
            )
            .scalars()
            .first()
        )
        payload.append(contact_to_read(contact, latest_message))
    return payload


@router.get("/contacts/{contact_id}")
def get_contact_detail(contact_id: int, db: Session = Depends(get_db)):
    contact = get_contact_or_404(db, contact_id)
    messages = db.execute(select(Message).where(Message.contact_id == contact.id).order_by(Message.created_at.desc())).scalars().all()
    replies = db.execute(select(Reply).where(Reply.contact_id == contact.id).order_by(Reply.received_at.desc())).scalars().all()
    return {
        "id": contact.id,
        "name": contact.name,
        "title": contact.title,
        "company_id": contact.company_id,
        "company_name": contact.company.name,
        "email": contact.email,
        "phone": contact.phone,
        "linkedin_url": contact.linkedin_url,
        "do_not_contact": contact.do_not_contact,
        "added_at": contact.added_at,
        "source": contact.source,
        "source_provider": contact.source_provider,
        "source_record_id": contact.source_record_id,
        "apollo_person_id": contact.apollo_person_id,
        "verification_status": contact.verification_status,
        "last_sync": contact.last_sync,
        "lead_score": contact.lead_score,
        "contact_priority": contact.contact_priority,
        "recommended_primary_contact": contact.recommended_primary_contact,
        "fallback_contact_used": contact.fallback_contact_used,
        "contact_selection_reason": contact.contact_selection_reason,
        "messages": [
            {
                "id": message.id,
                "subject": message.subject,
                "body": message.body,
                "status": message.status,
                "sent_at": message.sent_at,
                "sequence_step": message.sequence_step,
                "follow_up_at": message.follow_up_at,
                "mailbox_name": message.mailbox.name if message.mailbox else None,
                "campaign_name": message.campaign.name if message.campaign else None,
                "reply_count": len(message.replies),
            }
            for message in messages
        ],
        "replies": [
            {
                "id": reply.id,
                "message_id": reply.message_id,
                "body": reply.body,
                "received_at": reply.received_at,
                "outcome": reply.outcome,
            }
            for reply in replies
        ],
    }


@router.post("/contacts", response_model=ContactRead)
def create_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    get_company_or_404(db, payload.company_id)
    contact = Contact(
        name=payload.name,
        title=payload.title,
        company_id=payload.company_id,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
        linkedin_url=payload.linkedin_url,
        source=payload.source,
    )
    db.add(contact)
    db.flush()
    add_audit(
        db,
        entity_type="contact",
        entity_id=str(contact.id),
        action="created",
        reason=f"Contact added manually from {payload.source}.",
        metadata={"name": payload.name, "title": payload.title, "email": payload.email, "company_id": payload.company_id},
        contact_id=contact.id,
    )
    db.commit()
    db.refresh(contact)
    return contact_to_read(contact)


@router.put("/contacts/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    contact = get_contact_or_404(db, contact_id)
    if payload.company_id is not None:
        company = get_company_or_404(db, payload.company_id)
    elif payload.company_name:
        company = db.execute(select(Company).where(Company.name == payload.company_name)).scalars().first()
        if company is None:
            company = Company(name=payload.company_name, industry="Unspecified", source="Manual", notes="")
            db.add(company)
            db.flush()
    else:
        company = contact.company
    contact.name = payload.name
    contact.title = payload.title
    contact.company_id = company.id
    contact.email = payload.email
    contact.phone = payload.phone
    contact.linkedin_url = payload.linkedin_url
    contact.do_not_contact = payload.do_not_contact
    add_audit(
        db,
        entity_type="contact",
        entity_id=str(contact.id),
        action="updated",
        reason="Contact edited from lead review.",
        metadata={
            "name": payload.name,
            "title": payload.title,
            "company_id": company.id,
            "do_not_contact": payload.do_not_contact,
        },
        contact_id=contact.id,
    )
    db.commit()
    db.refresh(contact)
    return contact_to_read(contact)


@router.post("/contacts/import")
async def import_contacts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    frame = read_csv_upload(await file.read())
    inserted = 0
    skipped_duplicates = 0
    for row in frame.fillna("").to_dict(orient="records"):
        name = pick_field(row, ["name", "contact", "contact name", "person"])
        title = pick_field(row, ["title", "job title", "designation"])
        company_name = pick_field(row, ["company", "company name", "organization"])
        if not name or not title or not company_name:
            continue
        company = db.execute(select(Company).where(Company.name == company_name)).scalars().first()
        if not company:
            company = Company(
                name=company_name,
                industry=pick_field(row, ["industry", "sector"]) or "Unspecified",
                source=pick_field(row, ["source", "found via"]) or "CSV import",
                notes="Created through contact import",
            )
            db.add(company)
            db.flush()
        source = pick_field(row, ["source", "found via"]) or "CSV import"
        email = pick_field(row, ["email", "work email"]) or None
        phone = pick_field(row, ["phone", "mobile", "work phone"]) or None
        linkedin_url = pick_field(row, ["linkedin", "linkedin url", "profile url"]) or None

        duplicate = find_contact_for_discovery(
            db,
            company_id=company.id,
            apollo_person_id=None,
            email=email,
            name=name,
            title=title,
        )
        if duplicate:
            skipped_duplicates += 1
            continue

        contact = Contact(
            name=name,
            title=title,
            company_id=company.id,
            source=source,
            email=email,
            phone=phone,
            linkedin_url=linkedin_url,
        )
        db.add(contact)
        db.flush()
        add_audit(
            db,
            entity_type="contact",
            entity_id=str(contact.id),
            action="imported",
            reason="Imported from CSV.",
            metadata={"row": row, "company_name": company_name},
            contact_id=contact.id,
        )
        inserted += 1
    db.commit()
    return {"imported": inserted, "skipped_duplicates": skipped_duplicates}


@router.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    contact = get_contact_or_404(db, contact_id)
    db.delete(contact)
    db.commit()
    return {"deleted": contact_id}


@router.get("/campaigns", response_model=list[CampaignRead])
def list_campaigns(db: Session = Depends(get_db)):
    campaigns = db.execute(select(Campaign).order_by(Campaign.created_at.desc())).scalars().all()
    payload = []
    for campaign in campaigns:
        payload.append(
            CampaignRead(
                id=campaign.id,
                name=campaign.name,
                notes=campaign.notes,
                company_name=campaign.company.name if campaign.company else None,
                message_count=len(campaign.messages),
            )
        )
    return payload


@router.post("/campaigns", response_model=CampaignRead)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    company = get_company_or_404(db, payload.company_id) if payload.company_id else None
    campaign = Campaign(name=payload.name, notes=payload.notes, company_id=company.id if company else None)
    db.add(campaign)
    db.flush()
    add_audit(
        db,
        entity_type="campaign",
        entity_id=str(campaign.id),
        action="created",
        reason="Campaign created manually.",
        metadata={"name": payload.name, "company_id": payload.company_id},
        campaign_id=campaign.id,
    )
    db.commit()
    db.refresh(campaign)
    return CampaignRead(
        id=campaign.id,
        name=campaign.name,
        notes=campaign.notes,
        company_name=campaign.company.name if campaign.company else None,
        message_count=0,
    )


@router.get("/mailboxes", response_model=list[MailboxRead])
def list_mailboxes(db: Session = Depends(get_db)):
    mailboxes = db.execute(select(Mailbox).order_by(Mailbox.created_at.desc())).scalars().all()
    return [
        MailboxRead(
            id=mailbox.id,
            name=mailbox.name,
            email=mailbox.email,
            daily_limit=mailbox.daily_limit,
            active=mailbox.active,
            sent_today=daily_sent_count(db, mailbox.id),
        )
        for mailbox in mailboxes
    ]


@router.get("/daily-targets", response_model=list[DailyLeadTargetRead])
def get_daily_targets(db: Session = Depends(get_db)):
    return daily_target_snapshot(db)


@router.put("/daily-targets", response_model=list[DailyLeadTargetRead])
def update_daily_targets(
    payload: list[DailyLeadTargetUpdate],
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    if payload:
        upsert_daily_targets(db, payload)
    return daily_target_snapshot(db)


@router.get("/settings")
def get_workspace_settings(db: Session = Depends(get_db)):
    return settings_snapshot(db)


@router.put("/settings")
def update_workspace_settings(
    payload: list[WorkspaceSettingUpdate],
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    return upsert_workspace_settings(db, payload)


@router.post("/mailboxes", response_model=MailboxRead)
def create_mailbox(
    payload: MailboxCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    mailbox = Mailbox(
        name=payload.name,
        email=str(payload.email),
        daily_limit=payload.daily_limit or settings.default_daily_send_limit,
        active=payload.active,
    )
    db.add(mailbox)
    db.flush()
    add_audit(
        db,
        entity_type="mailbox",
        entity_id=str(mailbox.id),
        action="created",
        reason="Mailbox created for throttled sending.",
        metadata={"email": payload.email, "daily_limit": mailbox.daily_limit},
        mailbox_id=mailbox.id,
    )
    db.commit()
    db.refresh(mailbox)
    return MailboxRead(
        id=mailbox.id,
        name=mailbox.name,
        email=mailbox.email,
        daily_limit=mailbox.daily_limit,
        active=mailbox.active,
        sent_today=0,
    )


@router.get("/messages")
def list_messages(db: Session = Depends(get_db)):
    messages = db.execute(select(Message).order_by(Message.updated_at.desc())).scalars().all()
    return [
        {
            "id": message.id,
            "contact_id": message.contact_id,
            "contact_name": message.contact.name,
            "company_name": message.contact.company.name,
            "subject": message.subject,
            "status": message.status,
            "mailbox_name": message.mailbox.name if message.mailbox else None,
            "sent_at": message.sent_at,
            "follow_up_at": message.follow_up_at,
            "sequence_step": message.sequence_step,
            "reply_count": len(message.replies),
        }
        for message in messages
    ]


@router.get("/drafts", response_model=list[DraftRead])
def list_email_drafts(db: Session = Depends(get_db)):
    return [DraftRead(**draft) for draft in list_drafts(db)]


@router.post("/drafts/generate", response_model=DraftRead)
def generate_email_draft(
    payload: DraftGenerateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    contact = get_contact_or_404(db, payload.lead_id)
    try:
        draft = create_draft(db, payload=payload, contact=contact)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DraftRead(
        id=draft.id,
        contact_id=draft.contact_id,
        contact_name=draft.contact.name,
        company_name=draft.contact.company.name,
        campaign_id=draft.campaign_id,
        campaign_name=draft.campaign.name if draft.campaign else None,
        subject=draft.subject,
        body=draft.body,
        status=draft.status,
        sequence_step=draft.sequence_step,
        updated_at=draft.updated_at,
    )


@router.put("/drafts/{draft_id}", response_model=DraftRead)
def save_email_draft(
    draft_id: int,
    payload: DraftUpdateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    try:
        draft = update_draft(db, draft_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DraftRead(
        id=draft.id,
        contact_id=draft.contact_id,
        contact_name=draft.contact.name,
        company_name=draft.contact.company.name,
        campaign_id=draft.campaign_id,
        campaign_name=draft.campaign.name if draft.campaign else None,
        subject=draft.subject,
        body=draft.body,
        status=draft.status,
        sequence_step=draft.sequence_step,
        updated_at=draft.updated_at,
    )


@router.post("/messages/send-bulk")
def send_bulk(
    payload: BulkSendRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    try:
        return send_bulk_messages(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/messages/draft")
def create_message_draft(
    payload: MessageDraftCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    contact = get_contact_or_404(db, payload.contact_id)
    if contact.do_not_contact:
        raise HTTPException(status_code=400, detail="This contact is marked do not contact.")
    if payload.campaign_id:
        campaign = db.get(Campaign, payload.campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
    message = Message(
        contact_id=payload.contact_id,
        campaign_id=payload.campaign_id,
        subject=payload.subject,
        body=payload.body,
        sequence_step=max(0, payload.sequence_step),
        status="draft",
    )
    db.add(message)
    db.flush()
    add_audit(
        db,
        entity_type="message",
        entity_id=str(message.id),
        action="created",
        reason="Draft message created manually.",
        metadata={"contact_id": payload.contact_id, "subject": payload.subject, "sequence_step": payload.sequence_step},
        message_id=message.id,
    )
    db.commit()
    return {"message_id": message.id}


@router.post("/messages/{message_id}/send")
def send_message(
    message_id: int,
    payload: MessageSendCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    message = get_message_or_404(db, message_id)
    contact = message.contact
    if contact.do_not_contact:
        raise HTTPException(status_code=400, detail="This contact is marked do not contact.")
    mailbox = db.get(Mailbox, payload.mailbox_id)
    if not mailbox or not mailbox.active:
        raise HTTPException(status_code=400, detail="Select an active mailbox.")
    if daily_sent_count(db, mailbox.id) >= mailbox.daily_limit:
        raise HTTPException(status_code=400, detail="Daily send limit reached for this mailbox.")
    message.status = "sent"
    message.sent_at = now_utc()
    message.mailbox_id = mailbox.id
    message.body = ensure_opt_out_line(message.body)
    add_audit(
        db,
        entity_type="message",
        entity_id=str(message.id),
        action="sent",
        reason=f"Marked sent manually via {mailbox.name}.",
        metadata={"mailbox_id": mailbox.id},
        message_id=message.id,
        mailbox_id=mailbox.id,
    )
    db.commit()
    return {"message_id": message.id, "status": message.status}


@router.post("/replies")
def log_reply(
    payload: ReplyCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    message = get_message_or_404(db, payload.message_id)
    contact = get_contact_or_404(db, payload.contact_id)
    reply = Reply(
        message_id=message.id,
        contact_id=contact.id,
        body=payload.body,
        outcome=payload.outcome,
    )
    message.status = "replied"
    db.add(reply)
    add_audit(
        db,
        entity_type="reply",
        entity_id=str(reply.id),
        action="replied",
        reason="Reply recorded manually.",
        metadata={"outcome": payload.outcome},
        contact_id=contact.id,
        message_id=message.id,
    )
    db.commit()
    return {"reply_id": reply.id}


@router.post("/messages/{message_id}/follow-up")
def schedule_follow_up(
    message_id: int,
    payload: FollowUpCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    message = get_message_or_404(db, message_id)
    message.follow_up_at = payload.follow_up_at
    add_audit(
        db,
        entity_type="message",
        entity_id=str(message.id),
        action="scheduled_follow_up",
        reason="Follow-up date added manually.",
        metadata={"follow_up_at": payload.follow_up_at.isoformat()},
        contact_id=payload.contact_id,
        message_id=message.id,
    )
    db.commit()
    return {"message_id": message.id, "follow_up_at": message.follow_up_at}


@router.post("/messages/{message_id}/bounce")
def mark_bounced(
    message_id: int,
    contact_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    message = get_message_or_404(db, message_id)
    contact = get_contact_or_404(db, contact_id)
    message.status = "bounced"
    contact.do_not_contact = True
    add_audit(
        db,
        entity_type="message",
        entity_id=str(message.id),
        action="bounced",
        reason="Marked as bounced; contact set to do not contact.",
        metadata={},
        contact_id=contact.id,
        message_id=message.id,
    )
    db.commit()
    return {"message_id": message.id, "status": message.status}


@router.get("/companies/export/csv")
def export_companies_csv(db: Session = Depends(get_db)):
    data = [
        {
            "name": company.name,
            "industry": company.industry,
            "source": company.source,
            "notes": company.notes,
            "product_fit": ", ".join(company_product_fits(company)),
        }
        for company in db.execute(select(Company)).scalars().all()
    ]
    return Response(pd.DataFrame(data).to_csv(index=False), media_type="text/csv")


@router.get("/contacts/export/csv")
def export_contacts_csv(db: Session = Depends(get_db)):
    contacts = db.execute(
        select(Contact).options(selectinload(Contact.company).selectinload(Company.product_fits))
    ).scalars().all()
    data = [
        {
            "name": contact.name,
            "title": contact.title,
            "company": contact.company.name,
            "product_fit": ", ".join(company_product_fits(contact.company)),
            "discovery_profiles": ", ".join(contact_discovery_profiles(contact)),
            "source": contact.source,
            "email": contact.email,
            "phone": contact.phone,
            "linkedin_url": contact.linkedin_url,
        }
        for contact in contacts
    ]
    return Response(pd.DataFrame(data).to_csv(index=False), media_type="text/csv")
