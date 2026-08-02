from __future__ import annotations

from app.discovery.types import (
    DiscoveryCompanyCandidate,
    DiscoveryContactCandidate,
    DiscoveryScoreResult,
    ICPProductLine,
)


def _contains_any(haystack: str | None, needles: list[str]) -> bool:
    if not haystack:
        return False
    lowered = haystack.lower()
    return any(needle.lower() in lowered for needle in needles if needle)


def score_organization(
    icp: ICPProductLine,
    organization: DiscoveryCompanyCandidate,
    people: list[DiscoveryContactCandidate],
) -> DiscoveryScoreResult:
    rules = icp.lead_score_rules
    score = 0.0
    reasons: list[str] = []

    industry_match = _contains_any(organization.industry, icp.target_industries) or _contains_any(
        organization.description, icp.company_keywords
    ) or _contains_any(organization.name, icp.company_keywords)
    if industry_match:
        score += float(rules.get("industry_match", 0))
        reasons.append("industry/keyword match")

    keyword_match = _contains_any(organization.name, icp.company_keywords) or _contains_any(
        organization.description, icp.company_keywords
    )
    if keyword_match:
        score += float(rules.get("keyword_match", 0))
        reasons.append("keyword match")

    company_size_fit = False
    if organization.employee_count is not None:
        company_size_fit = icp.employee_min <= organization.employee_count <= icp.employee_max
    if company_size_fit:
        score += float(rules.get("company_size_fit", 0))
        reasons.append("company size fit")

    decision_maker_found = any(_contains_any(person.title, icp.target_titles + icp.preferred_titles) for person in people)
    if decision_maker_found:
        score += float(rules.get("decision_maker_found", 0))
        reasons.append("decision maker found")

    verified_contact_present = any((person.email_status or "").lower() == "verified" for person in people)
    if verified_contact_present:
        score += float(rules.get("verified_contact_present", 0))
        reasons.append("verified contact present")

    import_threshold = float(rules.get("import_threshold", 60))
    manual_review_threshold = float(rules.get("manual_review_threshold", 35))
    has_sufficient_data = bool(organization.name and (organization.industry or organization.description))
    needs_manual_review = not has_sufficient_data or (score >= manual_review_threshold and score < import_threshold)

    if score >= import_threshold and decision_maker_found and not needs_manual_review:
        status = "qualified"
    elif needs_manual_review:
        status = "manual_review"
    else:
        status = "rejected"

    return DiscoveryScoreResult(
        score=score,
        status=status,
        needs_manual_review=needs_manual_review,
        reasons=reasons,
        matched_industry=industry_match,
        matched_keyword=keyword_match,
        matched_company_size=company_size_fit,
        matched_decision_maker=decision_maker_found,
        verified_contact_present=verified_contact_present,
    )


def score_person(icp: ICPProductLine, person: DiscoveryContactCandidate) -> DiscoveryScoreResult:
    rules = icp.lead_score_rules
    score = 0.0
    reasons: list[str] = []

    title_match = _contains_any(person.title, icp.target_titles)
    preferred_title_match = _contains_any(person.title, icp.preferred_titles)
    if title_match:
        score += float(rules.get("decision_maker_found", 0))
        reasons.append("target title match")
    if preferred_title_match:
        score += 5
        reasons.append("preferred title match")

    verified_contact_present = (person.email_status or "").lower() == "verified"
    if verified_contact_present:
        score += float(rules.get("verified_contact_present", 0))
        reasons.append("verified contact present")

    has_sufficient_data = bool(person.name and person.title)
    manual_review_threshold = float(rules.get("manual_review_threshold", 35))
    import_threshold = float(rules.get("import_threshold", 60))
    needs_manual_review = not has_sufficient_data or (score >= manual_review_threshold and score < import_threshold)

    if score >= import_threshold and title_match and not needs_manual_review:
        status = "qualified"
    elif needs_manual_review:
        status = "manual_review"
    else:
        status = "rejected"

    return DiscoveryScoreResult(
        score=score,
        status=status,
        needs_manual_review=needs_manual_review,
        reasons=reasons,
        matched_decision_maker=title_match,
        verified_contact_present=verified_contact_present,
    )
