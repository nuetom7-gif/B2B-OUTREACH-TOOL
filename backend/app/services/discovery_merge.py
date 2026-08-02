from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Company, CompanyProductFit, Contact
from app.services.outreach import add_audit


def _is_missing(value) -> bool:
    return value is None or value == ""


def find_company_for_discovery(
    db: Session,
    *,
    source_provider: str | None = None,
    source_record_id: str | None = None,
    apollo_organization_id: str | None = None,
    name: str,
) -> Company | None:
    if source_provider and source_record_id:
        company = db.execute(
            select(Company).where(
                Company.source_provider == source_provider,
                Company.source_record_id == source_record_id,
            )
        ).scalars().first()
        if company:
            return company
    if apollo_organization_id:
        company = db.execute(select(Company).where(Company.apollo_organization_id == apollo_organization_id)).scalars().first()
        if company:
            return company
    return db.execute(select(Company).where(Company.name == name)).scalars().first()


def merge_company_fields(company: Company, source_company: dict) -> list[str]:
    merged: list[str] = []
    field_map = {
        "industry": source_company.get("industry"),
        "notes": source_company.get("notes"),
        "apollo_organization_id": source_company.get("apollo_organization_id"),
        "apollo_last_updated": source_company.get("apollo_last_updated"),
        "last_sync": source_company.get("last_sync"),
        "sync_status": source_company.get("sync_status"),
        "needs_manual_review": source_company.get("needs_manual_review"),
        "lead_score": source_company.get("lead_score"),
        "owner_id": source_company.get("owner_id"),
        "assignment_status": source_company.get("assignment_status"),
        "assigned_at": source_company.get("assigned_at"),
        "assignment_source": source_company.get("assignment_source"),
    }
    for attr, value in field_map.items():
        if _is_missing(value):
            continue
        current = getattr(company, attr, None)
        if _is_missing(current):
            setattr(company, attr, value)
            merged.append(attr)
    if source_company.get("source") and _is_missing(company.source):
        company.source = source_company["source"]
        merged.append("source")
    return merged


def upsert_company_from_discovery(db: Session, *, company_payload: dict, source: str = "apollo_auto", source_provider: str | None = None) -> tuple[Company, bool, list[str]]:
    company = find_company_for_discovery(
        db,
        source_provider=source_provider,
        source_record_id=company_payload.get("source_record_id"),
        apollo_organization_id=company_payload.get("apollo_organization_id"),
        name=company_payload["name"],
    )
    created = False
    merged_fields: list[str] = []

    if not company:
        company = Company(
            name=company_payload["name"],
            industry=company_payload.get("industry") or "Unspecified",
            source=source,
            source_provider=source_provider,
            source_record_id=company_payload.get("source_record_id"),
            notes=company_payload.get("notes") or "",
            apollo_organization_id=company_payload.get("apollo_organization_id"),
            apollo_last_updated=company_payload.get("apollo_last_updated"),
            last_sync=company_payload.get("last_sync"),
            sync_status=company_payload.get("sync_status") or "synced",
            needs_manual_review=bool(company_payload.get("needs_manual_review", False)),
            owner_id=company_payload.get("owner_id"),
            assignment_status=company_payload.get("assignment_status") or "unassigned",
            assigned_at=company_payload.get("assigned_at"),
            assignment_source=company_payload.get("assignment_source"),
            lead_score=int(company_payload.get("lead_score") or 0),
        )
        db.add(company)
        db.flush()
        created = True
    else:
        merged_fields = merge_company_fields(company, company_payload)
        if _is_missing(company.source_provider) and source_provider:
            company.source_provider = source_provider
            merged_fields.append("source_provider")
        if _is_missing(company.source_record_id) and company_payload.get("source_record_id"):
            company.source_record_id = company_payload["source_record_id"]
            merged_fields.append("source_record_id")
        if not _is_missing(company.source) and source == "apollo_auto" and _is_missing(company_payload.get("source")):
            pass

    fits = company_payload.get("product_fits") or []
    existing_products = {fit.product for fit in company.product_fits}
    for product in fits:
        if product not in existing_products:
            db.add(CompanyProductFit(company_id=company.id, product=product))
            existing_products.add(product)
            merged_fields.append("product_fit")

    if created:
        add_audit(
            db,
            entity_type="company",
            entity_id=str(company.id),
            action="created",
            reason="Company auto-created during discovery.",
            metadata=company_payload,
            company_id=company.id,
        )
    elif merged_fields:
        add_audit(
            db,
            entity_type="company",
            entity_id=str(company.id),
            action="merged",
            reason="Company merged with discovery data.",
            metadata={"merged_fields": merged_fields, "source": source},
            company_id=company.id,
        )

    return company, created, merged_fields


def find_contact_for_discovery(
    db: Session,
    *,
    company_id: int,
    source_provider: str | None = None,
    source_record_id: str | None = None,
    apollo_person_id: str | None,
    email: str | None,
    name: str,
    title: str,
) -> Contact | None:
    stmt = select(Contact).where(Contact.company_id == company_id)
    if source_provider and source_record_id:
        contact = db.execute(
            stmt.where(Contact.source_provider == source_provider, Contact.source_record_id == source_record_id)
        ).scalars().first()
        if contact:
            return contact
    if apollo_person_id:
        contact = db.execute(stmt.where(Contact.apollo_person_id == apollo_person_id)).scalars().first()
        if contact:
            return contact
    if email:
        contact = db.execute(stmt.where(Contact.email == email)).scalars().first()
        if contact:
            return contact
    return db.execute(stmt.where(Contact.name == name, Contact.title == title)).scalars().first()


def find_blocked_contact_for_discovery(
    db: Session,
    *,
    company_name: str,
    source_provider: str | None,
    source_record_id: str | None,
    apollo_organization_id: str | None,
    contact_source_record_id: str | None,
    apollo_person_id: str | None,
    email: str | None,
    name: str,
    title: str,
) -> Contact | None:
    company = find_company_for_discovery(
        db,
        source_provider=source_provider,
        source_record_id=source_record_id,
        apollo_organization_id=apollo_organization_id,
        name=company_name,
    )
    if not company:
        return None
    contact = find_contact_for_discovery(
        db,
        company_id=company.id,
        source_provider=source_provider,
        source_record_id=contact_source_record_id,
        apollo_person_id=apollo_person_id,
        email=email,
        name=name,
        title=title,
    )
    if contact and contact.do_not_contact:
        return contact
    return None


def merge_contact_fields(contact: Contact, source_contact: dict) -> list[str]:
    merged: list[str] = []
    field_map = {
        "apollo_person_id": source_contact.get("apollo_person_id"),
        "verification_status": source_contact.get("verification_status"),
        "last_sync": source_contact.get("last_sync"),
        "lead_score": source_contact.get("lead_score"),
        "email": source_contact.get("email"),
        "phone": source_contact.get("phone"),
        "linkedin_url": source_contact.get("linkedin_url"),
        "source": source_contact.get("source"),
    }
    for attr, value in field_map.items():
        if _is_missing(value):
            continue
        current = getattr(contact, attr, None)
        if _is_missing(current):
            setattr(contact, attr, value)
            merged.append(attr)
    return merged


def upsert_contact_from_discovery(
    db: Session,
    *,
    company: Company,
    contact_payload: dict,
    source: str = "apollo_auto",
    source_provider: str | None = None,
) -> tuple[Contact, bool, list[str]]:
    contact = find_contact_for_discovery(
        db,
        company_id=company.id,
        source_provider=source_provider,
        source_record_id=contact_payload.get("source_record_id"),
        apollo_person_id=contact_payload.get("apollo_person_id"),
        email=contact_payload.get("email"),
        name=contact_payload["name"],
        title=contact_payload["title"],
    )
    created = False
    merged_fields: list[str] = []

    if not contact:
        contact = Contact(
            name=contact_payload["name"],
            title=contact_payload["title"],
            company_id=company.id,
            email=contact_payload.get("email"),
            phone=contact_payload.get("phone"),
            linkedin_url=contact_payload.get("linkedin_url"),
            source=source,
            source_provider=source_provider,
            source_record_id=contact_payload.get("source_record_id"),
            apollo_person_id=contact_payload.get("apollo_person_id"),
            verification_status=contact_payload.get("verification_status") or "unknown",
            last_sync=contact_payload.get("last_sync"),
            lead_score=int(contact_payload.get("lead_score") or 0),
        )
        db.add(contact)
        db.flush()
        created = True
    else:
        merged_fields = merge_contact_fields(contact, contact_payload)
        if _is_missing(contact.source_provider) and source_provider:
            contact.source_provider = source_provider
            merged_fields.append("source_provider")
        if _is_missing(contact.source_record_id) and contact_payload.get("source_record_id"):
            contact.source_record_id = contact_payload["source_record_id"]
            merged_fields.append("source_record_id")
        if _is_missing(contact.source):
            contact.source = source
            merged_fields.append("source")

    if created:
        add_audit(
            db,
            entity_type="contact",
            entity_id=str(contact.id),
            action="created",
            reason="Contact auto-created during discovery.",
            metadata=contact_payload,
            contact_id=contact.id,
        )
    elif merged_fields:
        add_audit(
            db,
            entity_type="contact",
            entity_id=str(contact.id),
            action="merged",
            reason="Contact merged with discovery data.",
            metadata={"merged_fields": merged_fields, "source": source},
            contact_id=contact.id,
        )

    return contact, created, merged_fields
