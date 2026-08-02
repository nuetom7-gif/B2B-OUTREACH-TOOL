from datetime import datetime, timezone
import json

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.base import AuditEvent, Campaign, Company, CompanyProductFit, Contact, Mailbox, Message, Reply

OPT_OUT_LINE = "Reply STOP to stop hearing from us."

settings = get_settings()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def add_audit(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    reason: str,
    metadata: dict | None = None,
    company_id: int | None = None,
    contact_id: int | None = None,
    campaign_id: int | None = None,
    message_id: int | None = None,
    mailbox_id: int | None = None,
) -> None:
    db.add(
        AuditEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            reason=reason,
            metadata_json=json.dumps(metadata or {}, default=str),
            company_id=company_id,
            contact_id=contact_id,
            campaign_id=campaign_id,
            message_id=message_id,
            mailbox_id=mailbox_id,
        )
    )


def ensure_opt_out_line(body: str) -> str:
    if "reply stop" in body.lower():
        return body.strip()
    return f"{body.strip()}\n\n{OPT_OUT_LINE}"


def daily_sent_count(db: Session, mailbox_id: int) -> int:
    start = now_utc().replace(hour=0, minute=0, second=0, microsecond=0)
    stmt = select(func.count(Message.id)).where(
        Message.mailbox_id == mailbox_id,
        Message.status == "sent",
        Message.sent_at >= start,
    )
    return db.scalar(stmt) or 0


def company_product_fits(company: Company) -> list[str]:
    return [fit.product for fit in company.product_fits]


def company_contact_count(db: Session, company_id: int) -> int:
    return db.scalar(select(func.count(Contact.id)).where(Contact.company_id == company_id)) or 0


def product_breakdown(db: Session) -> list[dict]:
    rows = db.execute(
        select(CompanyProductFit.product, func.count(CompanyProductFit.id)).group_by(CompanyProductFit.product)
    ).all()
    return [{"product": product, "count": count} for product, count in rows]


def recent_messages(db: Session, limit: int = 6) -> list[dict]:
    rows = (
        db.execute(
            select(Message, Contact.name, Company.name, Mailbox.name)
            .join(Contact, Message.contact_id == Contact.id)
            .join(Company, Contact.company_id == Company.id)
            .join(Mailbox, Message.mailbox_id == Mailbox.id, isouter=True)
            .order_by(Message.updated_at.desc())
            .limit(limit)
        )
        .all()
    )
    payload = []
    for message, contact_name, company_name, mailbox_name in rows:
        payload.append(
            {
                "id": message.id,
                "subject": message.subject,
                "status": message.status,
                "contact_name": contact_name,
                "company_name": company_name,
                "mailbox_name": mailbox_name,
            }
        )
    return payload
