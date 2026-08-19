from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
import contextlib
import json
import smtplib
from email.message import EmailMessage
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.discovery.config_loader import load_icp_config
from app.discovery.repository import todays_api_calls_used
from app.models.base import (
    Campaign,
    Company,
    CompanyProductFit,
    Contact,
    DailyLeadTarget,
    Mailbox,
    Message,
    Reply,
    WorkspaceSetting,
)
from app.schemas import (
    BulkSendRequest,
    DailyLeadTargetUpdate,
    DraftGenerateRequest,
    DraftUpdateRequest,
    WorkspaceSettingUpdate,
)
from app.services.outreach import add_audit, daily_sent_count, ensure_opt_out_line, now_utc, recent_messages


def _today_start() -> datetime:
    return now_utc().replace(hour=0, minute=0, second=0, microsecond=0)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _ensure_daily_target_defaults(db: Session) -> list[DailyLeadTarget]:
    existing = {row.product_segment: row for row in db.execute(select(DailyLeadTarget)).scalars().all()}
    changed = False
    # Configuration is the only portfolio authority. Profiles can share a
    # division, so retain first-seen order while creating one target per division.
    enabled_segments = list(
        dict.fromkeys(profile.product_name for profile in load_icp_config() if profile.enabled)
    )
    for segment in enabled_segments:
        if segment not in existing:
            db.add(
                DailyLeadTarget(
                    product_segment=segment,
                    target_leads_per_day=60,
                    companies_per_run=30,
                    contacts_per_company=2,
                    max_emails_per_batch=60,
                    active=True,
                )
            )
            changed = True
    if changed:
        db.flush()
    return db.execute(select(DailyLeadTarget).order_by(DailyLeadTarget.product_segment.asc())).scalars().all()


def list_daily_targets(db: Session) -> list[DailyLeadTarget]:
    targets = _ensure_daily_target_defaults(db)
    db.commit()
    return targets


def upsert_daily_targets(db: Session, payloads: list[DailyLeadTargetUpdate]) -> list[DailyLeadTarget]:
    existing = {row.product_segment: row for row in db.execute(select(DailyLeadTarget)).scalars().all()}
    results: list[DailyLeadTarget] = []
    for payload in payloads:
        target = existing.get(payload.product_segment)
        if target is None:
            target = DailyLeadTarget(product_segment=payload.product_segment)
            db.add(target)
        target.target_leads_per_day = payload.target_leads_per_day
        target.companies_per_run = payload.companies_per_run
        target.contacts_per_company = payload.contacts_per_company
        target.max_emails_per_batch = payload.max_emails_per_batch
        target.active = payload.active
        target.default_campaign_id = payload.default_campaign_id
        target.default_mailbox_id = payload.default_mailbox_id
        results.append(target)
    db.commit()
    return results


def list_workspace_settings(db: Session) -> dict[str, str]:
    settings = {row.key: row.value for row in db.execute(select(WorkspaceSetting)).scalars().all()}
    return settings


def upsert_workspace_settings(db: Session, payloads: list[WorkspaceSettingUpdate]) -> dict[str, str]:
    existing = {row.key: row for row in db.execute(select(WorkspaceSetting)).scalars().all()}
    for payload in payloads:
        setting = existing.get(payload.key)
        if setting is None:
            setting = WorkspaceSetting(key=payload.key, value=payload.value)
            db.add(setting)
        else:
            setting.value = payload.value
        add_audit(
            db,
            entity_type="setting",
            entity_id=payload.key,
            action="updated",
            reason="Workspace setting updated from UI.",
            metadata={"key": payload.key, "value": payload.value},
        )
    db.commit()
    return list_workspace_settings(db)


def _count_contacts_for_segment(db: Session, segment: str) -> int:
    start = _today_start()
    return (
        db.scalar(
            select(func.count(func.distinct(Contact.id)))
            .select_from(Contact)
            .join(Company, Contact.company_id == Company.id)
            .join(CompanyProductFit, CompanyProductFit.company_id == Company.id)
            .where(Contact.added_at >= start, CompanyProductFit.product == segment)
        )
        or 0
    )


def _count_sent_today(db: Session) -> int:
    start = _today_start()
    return db.scalar(select(func.count(Message.id)).where(Message.status == "sent", Message.sent_at >= start)) or 0


def _count_replies_today(db: Session) -> int:
    start = _today_start()
    return db.scalar(select(func.count(Reply.id)).where(Reply.received_at >= start)) or 0


def _count_bounces_today(db: Session) -> int:
    start = _today_start()
    return db.scalar(
        select(func.count(Message.id)).where(Message.status == "bounced", Message.updated_at >= start)
    ) or 0


def _series_for_days(db: Session, model, date_field: str, *, days: int = 14, count_field=None) -> list[dict[str, Any]]:
    start = _today_start() - timedelta(days=days - 1)
    payload: list[dict[str, Any]] = []
    for day_offset in range(days):
        current_day = start + timedelta(days=day_offset)
        next_day = current_day + timedelta(days=1)
        stmt = select(func.count(count_field or model.id)).where(
            getattr(model, date_field) >= current_day,
            getattr(model, date_field) < next_day,
        )
        payload.append({"date": current_day.date().isoformat(), "count": db.scalar(stmt) or 0})
    return payload


def dashboard_stats(db: Session) -> dict[str, Any]:
    targets = list_daily_targets(db)
    today_leads: dict[str, dict[str, int]] = {}
    per_product_stats: list[dict[str, Any]] = []
    for target in targets:
        current = _count_contacts_for_segment(db, target.product_segment)
        today_leads[target.product_segment] = {
            "target": target.target_leads_per_day,
            "current": current,
            "remaining": max(0, target.target_leads_per_day - current),
        }
        per_product_stats.append(
            {
                "product_segment": target.product_segment,
                "target": target.target_leads_per_day,
                "current": current,
                "remaining": max(0, target.target_leads_per_day - current),
                "progress": 0 if target.target_leads_per_day <= 0 else round((current / target.target_leads_per_day) * 100, 1),
            }
        )

    today_emails = _count_sent_today(db)
    today_replies = _count_replies_today(db)
    today_bounces = _count_bounces_today(db)
    reply_rate = 0.0 if today_emails == 0 else today_replies / today_emails
    bounce_rate = 0.0 if today_emails == 0 else today_bounces / today_emails
    settings = get_settings()
    remaining_credits = max(0, settings.apollo_daily_call_limit - todays_api_calls_used(db))

    pending_drafts = db.scalar(select(func.count(Message.id)).where(Message.status == "draft")) or 0
    pending_reviews = db.scalar(select(func.count(Company.id)).where(Company.needs_manual_review.is_(True))) or 0
    do_not_contact_count = db.scalar(select(func.count(Contact.id)).where(Contact.do_not_contact.is_(True))) or 0
    active_mailboxes = db.scalar(select(func.count(Mailbox.id)).where(Mailbox.active.is_(True))) or 0
    total_contacts = db.scalar(select(func.count(Contact.id))) or 0

    daily_leads = _series_for_days(db, Contact, "added_at")
    daily_emails = _series_for_days(db, Message, "sent_at")
    daily_replies = _series_for_days(db, Reply, "received_at")

    funnel = {
        "contacts": total_contacts,
        "drafts": pending_drafts,
        "sent": today_emails,
        "replies": today_replies,
        "do_not_contact": do_not_contact_count,
    }

    return {
        "today_leads": today_leads,
        "today_emails_sent": today_emails,
        "today_replies": today_replies,
        "reply_rate": reply_rate,
        "bounce_rate": bounce_rate,
        "apollo_credits_remaining": remaining_credits,
        "pending_drafts": pending_drafts,
        "pending_reviews": pending_reviews,
        "do_not_contact_count": do_not_contact_count,
        "per_product_stats": per_product_stats,
        "daily_leads": daily_leads,
        "daily_emails": daily_emails,
        "daily_replies": daily_replies,
        "funnel": funnel,
        "recent_activity": recent_messages(db, limit=10),
        "active_mailboxes": active_mailboxes,
        "total_contacts": total_contacts,
    }


def _conversation_tone(tone: str) -> str:
    tone = tone.strip().lower()
    if tone in {"friendly", "warm"}:
        return "warm and conversational"
    if tone in {"direct", "plain"}:
        return "direct and concise"
    return "professional and helpful"


def _length_guidance(length: str) -> str:
    length = length.strip().lower()
    if length == "long":
        return "Write a fuller note with two short paragraphs and a clear call to action."
    if length == "medium":
        return "Write a balanced note with one short intro paragraph and one CTA paragraph."
    return "Write a short note with a tight introduction and one clear call to action."


def _local_draft_copy(contact: Contact, product_segment: str, tone: str, length: str) -> tuple[str, str]:
    subject = f"{product_segment} for {contact.company.name}"
    body = (
        f"Hi {contact.name},\n\n"
        f"I’m reaching out because {contact.company.name} looks like a strong fit for our {product_segment} offering.\n"
        f"{_conversation_tone(tone).capitalize()} and {_length_guidance(length).lower()}\n\n"
        "If it would help, I can share a quick example of how teams like yours are using this to improve outreach.\n\n"
        "Best,\n"
        "Yash Technology"
    )
    return subject, body


def _openai_draft_copy(contact: Contact, product_segment: str, tone: str, length: str) -> tuple[str, str] | None:
    settings = get_settings()
    if not settings.openai_api_key.strip():
        return None
    model = settings.openai_draft_model if hasattr(settings, "openai_draft_model") else "gpt-4.1-mini"
    prompt = (
        "Write a B2B outreach email draft.\n"
        f"Lead name: {contact.name}\n"
        f"Lead title: {contact.title}\n"
        f"Company: {contact.company.name}\n"
        f"Industry: {contact.company.industry}\n"
        f"Product segment: {product_segment}\n"
        f"Tone: {_conversation_tone(tone)}\n"
        f"Length: {length}\n"
        "Return JSON with subject and body."
    )
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You write concise, high-quality B2B outbound email drafts."},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.5,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        draft = json.loads(content)
        subject = str(draft.get("subject") or "").strip()
        body = str(draft.get("body") or "").strip()
        if subject and body:
            return subject, body
    except Exception:
        return None
    return None


def generate_draft_copy(contact: Contact, product_segment: str, tone: str, length: str) -> tuple[str, str]:
    draft = _openai_draft_copy(contact, product_segment, tone, length)
    if draft:
        return draft
    return _local_draft_copy(contact, product_segment, tone, length)


def create_draft(
    db: Session,
    *,
    payload: DraftGenerateRequest,
    contact: Contact,
    campaign_id: int | None = None,
) -> Message:
    if contact.do_not_contact:
        raise ValueError("This contact is marked do not contact.")
    if payload.campaign_id or campaign_id:
        campaign = db.get(Campaign, payload.campaign_id or campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
    subject, body = generate_draft_copy(contact, payload.product_segment, payload.tone, payload.length)
    message = Message(
        contact_id=contact.id,
        campaign_id=payload.campaign_id or campaign_id,
        subject=subject,
        body=body,
        sequence_step=0,
        status="draft",
    )
    db.add(message)
    db.flush()
    add_audit(
        db,
        entity_type="message",
        entity_id=str(message.id),
        action="draft_generated",
        reason="AI draft generated from lead review.",
        metadata={
            "contact_id": contact.id,
            "product_segment": payload.product_segment,
            "tone": payload.tone,
            "length": payload.length,
        },
        contact_id=contact.id,
        campaign_id=message.campaign_id,
        message_id=message.id,
    )
    db.commit()
    db.refresh(message)
    return message


def update_draft(db: Session, draft_id: int, payload: DraftUpdateRequest) -> Message:
    message = db.get(Message, draft_id)
    if not message:
        raise ValueError("Draft not found")
    if message.status not in {"draft", "queued"}:
        raise ValueError("Only draft messages can be edited")
    message.subject = payload.subject
    message.body = payload.body
    message.sequence_step = payload.sequence_step
    if payload.campaign_id is not None:
        campaign = db.get(Campaign, payload.campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        message.campaign_id = payload.campaign_id
    add_audit(
        db,
        entity_type="message",
        entity_id=str(message.id),
        action="draft_updated",
        reason="Draft updated from UI.",
        metadata={"sequence_step": payload.sequence_step},
        contact_id=message.contact_id,
        campaign_id=message.campaign_id,
        message_id=message.id,
    )
    db.commit()
    db.refresh(message)
    return message


def list_drafts(db: Session) -> list[dict[str, Any]]:
    drafts = db.execute(select(Message).where(Message.status == "draft").order_by(Message.updated_at.desc())).scalars().all()
    return [
        {
            "id": draft.id,
            "contact_id": draft.contact_id,
            "contact_name": draft.contact.name,
            "company_name": draft.contact.company.name,
            "campaign_id": draft.campaign_id,
            "campaign_name": draft.campaign.name if draft.campaign else None,
            "subject": draft.subject,
            "body": draft.body,
            "status": draft.status,
            "sequence_step": draft.sequence_step,
            "updated_at": draft.updated_at,
        }
        for draft in drafts
    ]


def _render_template(template: str, contact: Contact, product_segment: str | None) -> str:
    values = {
        "name": contact.name,
        "title": contact.title,
        "company": contact.company.name,
        "industry": contact.company.industry,
        "product_segment": product_segment or "",
    }
    return template.format_map(defaultdict(str, values))


def _smtp_settings() -> dict[str, str | int]:
    db_settings: dict[str, str] = {}
    return db_settings


def _try_send_smtp(subject: str, body: str, contact: Contact, mailbox: Mailbox) -> bool:
    settings = get_settings()
    if not settings.smtp_host.strip() or not settings.smtp_from.strip():
        return False
    if not contact.email:
        return False
    message = EmailMessage()
    message["From"] = settings.smtp_from or mailbox.email
    message["To"] = contact.email
    message["Subject"] = subject
    message.set_content(ensure_opt_out_line(body))
    if settings.smtp_user.strip():
        message["Reply-To"] = settings.smtp_user
    if settings.smtp_port == 465:
        server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30)
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
        if settings.smtp_port in {587, 25}:
            try:
                server.starttls()
            except Exception:
                pass
    try:
        if settings.smtp_user.strip() and settings.smtp_password.strip():
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
        return True
    finally:
        with contextlib.suppress(Exception):
            server.quit()


def send_bulk_messages(db: Session, payload: BulkSendRequest) -> dict[str, Any]:
    mailbox = db.get(Mailbox, payload.mailbox_id)
    if not mailbox or not mailbox.active:
        raise ValueError("Select an active mailbox.")
    if daily_sent_count(db, mailbox.id) >= mailbox.daily_limit:
        raise ValueError("Daily send limit reached for this mailbox.")

    contact_ids = list(dict.fromkeys(payload.contact_ids))
    if payload.limit is not None:
        contact_ids = contact_ids[: max(0, payload.limit)]
    if not contact_ids:
        raise ValueError("Select at least one contact.")

    sent = 0
    failed = 0
    skipped = 0
    errors: list[str] = []
    remaining_capacity = max(0, mailbox.daily_limit - daily_sent_count(db, mailbox.id))

    for contact_id in contact_ids:
        if sent >= remaining_capacity:
            skipped += 1
            errors.append("Mailbox daily limit reached before all contacts were processed.")
            break
        contact = db.get(Contact, contact_id)
        if not contact:
            failed += 1
            errors.append(f"Contact {contact_id} not found")
            continue
        if contact.do_not_contact:
            skipped += 1
            errors.append(f"Contact {contact.id} is marked do not contact")
            continue
        if not contact.email:
            skipped += 1
            errors.append(f"Contact {contact.id} has no email address")
            continue

        subject = _render_template(payload.subject, contact, payload.product_segment)
        body = _render_template(payload.body, contact, payload.product_segment)
        message = Message(
            contact_id=contact.id,
            campaign_id=payload.campaign_id,
            mailbox_id=mailbox.id,
            subject=subject,
            body=ensure_opt_out_line(body),
            status="sending",
            sequence_step=0,
        )
        db.add(message)
        db.flush()

        smtp_sent = False
        try:
            smtp_sent = _try_send_smtp(subject, body, contact, mailbox)
        except Exception as exc:
            failed += 1
            message.status = "failed"
            errors.append(f"SMTP send failed for contact {contact.id}: {exc}")
            add_audit(
                db,
                entity_type="message",
                entity_id=str(message.id),
                action="failed",
                reason="Bulk send failed while delivering through SMTP.",
                metadata={
                    "mailbox_id": mailbox.id,
                    "campaign_id": payload.campaign_id,
                    "product_segment": payload.product_segment,
                    "error": str(exc),
                },
                contact_id=contact.id,
                campaign_id=payload.campaign_id,
                message_id=message.id,
                mailbox_id=mailbox.id,
            )
            db.commit()
            continue

        message.status = "sent"
        message.sent_at = now_utc()

        add_audit(
            db,
            entity_type="message",
            entity_id=str(message.id),
            action="sent",
            reason="Bulk send triggered from UI.",
            metadata={
                "mailbox_id": mailbox.id,
                "smtp_sent": smtp_sent,
                "campaign_id": payload.campaign_id,
                "product_segment": payload.product_segment,
            },
            contact_id=contact.id,
            campaign_id=payload.campaign_id,
            message_id=message.id,
            mailbox_id=mailbox.id,
        )
        sent += 1
        db.commit()

    return {"sent": sent, "failed": failed, "skipped": skipped, "errors": errors}


def daily_target_snapshot(db: Session) -> list[dict[str, Any]]:
    targets = list_daily_targets(db)
    payload: list[dict[str, Any]] = []
    for target in targets:
        current = _count_contacts_for_segment(db, target.product_segment)
        payload.append(
            {
                "id": target.id,
                "product_segment": target.product_segment,
                "target_leads_per_day": target.target_leads_per_day,
                "companies_per_run": target.companies_per_run,
                "contacts_per_company": target.contacts_per_company,
                "max_emails_per_batch": target.max_emails_per_batch,
                "active": target.active,
                "default_campaign_id": target.default_campaign_id,
                "default_mailbox_id": target.default_mailbox_id,
                "today_leads": current,
            }
        )
    return payload


def settings_snapshot(db: Session) -> dict[str, Any]:
    settings = list_workspace_settings(db)
    return {
        "smtp_host": settings.get("smtp_host", ""),
        "smtp_port": _safe_int(settings.get("smtp_port"), 587),
        "smtp_user": settings.get("smtp_user", ""),
        "smtp_from": settings.get("smtp_from", ""),
        "default_campaign_id": _safe_int(settings.get("default_campaign_id"), 0) or None,
        "default_mailbox_id": _safe_int(settings.get("default_mailbox_id"), 0) or None,
        "max_emails_per_batch": _safe_int(settings.get("max_emails_per_batch"), 60),
    }
