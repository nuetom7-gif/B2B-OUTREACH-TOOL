from __future__ import annotations

from dataclasses import dataclass, field

from app.discovery.types import DiscoveryCompanyCandidate, DiscoveryContactCandidate


CONTACT_PRIORITY_TIERS: list[tuple[str, list[str]]] = [
    ("tier_1", ["Purchase Manager", "Procurement Manager", "Purchase Head", "Procurement Head", "Sourcing Manager"]),
    (
        "tier_2",
        [
            "Plant Head",
            "Plant Manager",
            "Factory Manager",
            "Works Manager",
            "Production Head",
            "Production Manager",
            "Operations Head",
            "Operations Manager",
        ],
    ),
    (
        "tier_3",
        [
            "Maintenance Head",
            "Maintenance Manager",
            "Engineering Head",
            "Engineering Manager",
            "EHS Head",
            "EHS Manager",
            "Safety Head",
            "Safety Manager",
            "Quality Head",
            "Quality Manager",
        ],
    ),
    (
        "tier_4",
        ["Owner", "Founder", "Managing Director", "CEO", "Director", "General Manager"],
    ),
]

FALLBACK_BUSINESS_TITLES = [
    "Manager",
    "Executive",
    "Administrator",
    "Office Manager",
    "HR Manager",
    "Sales Manager",
    "Business Development Manager",
    "Customer Support",
    "Reception",
    "Executive Assistant",
]

CONTACT_PRIORITY_RANKS = {
    "tier_1": 1,
    "tier_2": 2,
    "tier_3": 3,
    "tier_4": 4,
    "low": 5,
}

CONTACT_PRIORITY_POINTS = {
    "tier_1": 35,
    "tier_2": 25,
    "tier_3": 15,
    "tier_4": 8,
    "low": 2,
}


@dataclass(slots=True)
class ContactDiscoveryBatch:
    organization: DiscoveryCompanyCandidate
    contacts: list[DiscoveryContactCandidate] = field(default_factory=list)
    primary_contact: DiscoveryContactCandidate | None = None
    contact_status: str = "No Contact Found"
    fallback_contact_used: bool = False
    total_contacts_returned: int = 0
    primary_contact_reason: str | None = None
    diagnostic_requests: list[dict] = field(default_factory=list)
    diagnostic_responses: list[dict] = field(default_factory=list)
    zero_contact_reason: str | None = None


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def title_matches(title: str | None, candidates: list[str]) -> bool:
    normalized = _normalize(title)
    if not normalized:
        return False
    return any(_normalize(candidate) in normalized for candidate in candidates if candidate)


def match_priority_label(title: str | None) -> str | None:
    for label, titles in CONTACT_PRIORITY_TIERS:
        if title_matches(title, titles):
            return label
    if title_matches(title, FALLBACK_BUSINESS_TITLES):
        return "low"
    return None


def priority_rank(label: str | None) -> int:
    return CONTACT_PRIORITY_RANKS.get((label or "low").strip().lower(), CONTACT_PRIORITY_RANKS["low"])


def priority_points(label: str | None) -> int:
    return CONTACT_PRIORITY_POINTS.get((label or "low").strip().lower(), 0)


def contact_search_phases(icp=None) -> list[tuple[str, list[str], bool]]:
    configured = getattr(icp, "decision_maker_tiers", None) or {}
    phases = []
    for label, default_titles in CONTACT_PRIORITY_TIERS:
        titles = configured.get(label) or configured.get(label.replace("_", " ")) or default_titles
        phases.append((label, titles, False))
    fallback_titles = configured.get("tier_5") or configured.get("tier 5") or FALLBACK_BUSINESS_TITLES
    phases.append(("low", fallback_titles, True))
    return phases


def annotate_contact_priority(
    contact: DiscoveryContactCandidate,
    *,
    priority_label: str,
    fallback_contact_used: bool,
    selection_reason: str | None = None,
) -> DiscoveryContactCandidate:
    contact.contact_priority = priority_label
    contact.contact_priority_rank = priority_rank(priority_label)
    contact.fallback_contact_used = fallback_contact_used
    contact.contact_selection_reason = selection_reason
    return contact


def choose_primary_contact(
    contacts: list[DiscoveryContactCandidate],
    *,
    organization: DiscoveryCompanyCandidate,
) -> tuple[DiscoveryContactCandidate | None, str | None]:
    if not contacts:
        return None, None

    def sort_key(contact: DiscoveryContactCandidate) -> tuple[int, int, int, str, str]:
        verified = 1 if (contact.email_status or "").lower() == "verified" else 0
        priority = priority_rank(contact.contact_priority)
        matched_label = match_priority_label(contact.title) or contact.contact_priority or "low"
        return (
            priority,
            -priority_points(matched_label),
            -verified,
            (contact.name or "").lower(),
            (contact.title or "").lower(),
        )

    primary = sorted(contacts, key=sort_key)[0]
    reason = (
        f"Selected '{primary.title}' from {organization.name} as the highest-priority available contact "
        f"({primary.contact_priority or 'low'})."
    )
    if primary.fallback_contact_used:
        reason += " Fallback business-contact search was required."
    elif primary.contact_priority == "tier_1":
        reason += " Tier 1 purchase/procurement contact matched."
    elif primary.contact_priority == "tier_2":
        reason += " Tier 2 operations/plant contact matched."
    elif primary.contact_priority == "tier_3":
        reason += " Tier 3 maintenance/quality/safety contact matched."
    elif primary.contact_priority == "tier_4":
        reason += " Tier 4 owner/director-level contact matched."
    primary.recommended_primary_contact = True
    primary.contact_selection_reason = reason
    return primary, reason


def discover_contacts_for_organization(
    provider_manager,
    icp,
    organization: DiscoveryCompanyCandidate,
    *,
    max_contacts: int,
    per_page: int,
    before_search=None,
) -> ContactDiscoveryBatch:
    batch = ContactDiscoveryBatch(organization=organization)
    search_limit = max(1, min(max_contacts, per_page))

    ideal_contacts: list[DiscoveryContactCandidate] = []
    fallback_contacts: list[DiscoveryContactCandidate] = []
    seen_ids: set[str] = set()
    for label, titles, fallback_used in contact_search_phases(icp):
        page = 1
        collected: list[DiscoveryContactCandidate] = []
        while len(collected) < max_contacts:
            if callable(before_search):
                before_search()
            results = provider_manager.search_people(
                icp,
                organization,
                page=page,
                per_page=search_limit,
                title_filters=titles,
            )
            diagnostic = getattr(provider_manager, "last_search_diagnostic", None)
            if diagnostic:
                batch.diagnostic_requests.append(diagnostic.get("request", {}))
                batch.diagnostic_responses.append(diagnostic.get("response", {}))
            if not results:
                break
            for contact in results:
                if contact.provider_person_id not in seen_ids:
                    seen_ids.add(contact.provider_person_id)
                    collected.append(contact)
            if len(results) < search_limit:
                break
            page += 1

        annotated = [
            annotate_contact_priority(
                contact,
                priority_label=label,
                fallback_contact_used=fallback_used,
                selection_reason=(
                    "Fallback broad business-contact search used after no Tier 1-4 contacts were returned."
                    if fallback_used
                    else f"Matched {label.replace('_', ' ').title()} search titles."
                ),
            )
            for contact in collected
        ]
        if fallback_used:
            fallback_contacts.extend(annotated)
        else:
            ideal_contacts.extend(annotated)

        # Continue through all tiers so alternates are retained, but never exceed
        # the configured per-company contact cap.
        if len(ideal_contacts) >= max_contacts:
            break

    selected = (ideal_contacts or fallback_contacts)[:max_contacts]
    if selected:
        batch.fallback_contact_used = not ideal_contacts
        batch.contacts = selected
        batch.total_contacts_returned = len(selected)
        batch.contact_status = "Low Priority Contacts Found" if batch.fallback_contact_used else "Contacts Found"
        batch.primary_contact, batch.primary_contact_reason = choose_primary_contact(selected, organization=organization)
        return batch

    batch.fallback_contact_used = True
    batch.contacts = []
    batch.total_contacts_returned = 0
    batch.contact_status = "No Contact Found"
    batch.primary_contact = None
    batch.primary_contact_reason = "No Apollo contacts were returned after tiered and fallback searches."
    batch.zero_contact_reason = "Apollo returned zero contacts for every configured decision-maker tier and the Tier 5 fallback search."
    return batch
