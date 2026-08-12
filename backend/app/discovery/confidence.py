from __future__ import annotations

from typing import Any

from app.discovery.search_strategy import SearchStrategy
from app.discovery.industry_normalization import normalize_industry
from app.discovery.types import DiscoveryCompanyCandidate, ICPProductLine


CONFIDENCE_BANDS = (
    (70.0, "High Confidence"),
    (45.0, "Good Prospect"),
    (0.0, "Potential Prospect"),
)


def confidence_band(score: float) -> str:
    for minimum, label in CONFIDENCE_BANDS:
        if score >= minimum:
            return label
    return "Low Relevance"


def _text(organization: DiscoveryCompanyCandidate) -> str:
    return " ".join(
        str(value or "")
        for value in (organization.name, organization.industry, organization.description, organization.domain)
    ).lower()


def _apollo_description(organization: DiscoveryCompanyCandidate) -> str:
    """Combine Apollo's common summary fields without scraping the website."""
    raw = organization.source_metadata.get("apollo_raw_record", organization.source_metadata)
    if not isinstance(raw, dict):
        raw = {}
    return " ".join(
        str(value or "")
        for value in (
            organization.description,
            raw.get("description"),
            raw.get("short_description"),
            raw.get("headline"),
            raw.get("organization_summary"),
            raw.get("summary"),
        )
    ).lower()


def evaluate_discovery_confidence(
    icp: ICPProductLine,
    organization: DiscoveryCompanyCandidate,
    strategy: SearchStrategy,
) -> dict[str, Any]:
    rules = {
        "threshold": 30,
        "industry_match": 40,
        "product_keyword_match": 25,
        "description_match": 20,
        "website_match": 10,
        "employee_range_match": 5,
        "negative_keyword_penalty": 30,
        "missing_industry_penalty": 40,
        "missing_description_penalty": 20,
        "related_industry_family_match": 30,
        "manufacturing_family_match": 15,
        **(icp.discovery_confidence_rules or {}),
    }
    score = 0.0
    reasons: list[str] = []
    content = _text(organization)
    description = _apollo_description(organization)
    exact_labels = [strategy.industry] if strategy.industry else []
    exact_labels.extend(icp.exact_industries)
    industry_result = normalize_industry(icp, organization, exact_labels=exact_labels)
    if industry_result["match_type"] == "exact":
        score += float(rules["industry_match"])
        reasons.append("Industry exactly matched the focused search strategy.")
    elif industry_result["match_type"] == "related_family":
        score += float(rules["related_industry_family_match"])
        reasons.append("Industry matched a related ICP industry family.")
    elif industry_result["match_type"] == "manufacturing_family":
        score += float(rules["manufacturing_family_match"])
        reasons.append("Industry matched a relevant manufacturing family.")
    else:
        score -= float(rules["missing_industry_penalty"])
        reasons.append("No matching Apollo industry family was available.")
    keyword = (strategy.product_keyword or "").lower()
    if keyword and keyword in content:
        score += float(rules["product_keyword_match"])
        reasons.append(f"Product keyword matched: {strategy.product_keyword}.")
    description_terms = [keyword] + [
        item.lower()
        for item in (
            icp.product_keywords
            + icp.application_keywords
            + icp.manufacturing_keywords
            + icp.process_keywords
        )
        if item
    ]
    if any(term and term in description for term in description_terms):
        score += float(rules["description_match"])
        reasons.append("A configured product/application signal matched the Apollo description.")
    elif not description:
        score -= float(rules["missing_description_penalty"])
        reasons.append("Apollo returned no description or summary.")
    website_terms = [
        item.lower()
        for item in (icp.product_keywords + icp.application_keywords + icp.manufacturing_keywords)
        if item
    ]
    website_signal = " ".join((organization.domain or "", organization.name or "")).lower()
    if website_signal and any(term and term in website_signal for term in website_terms):
        score += float(rules["website_match"])
        reasons.append("The Apollo website/domain or company name contained a product signal.")
    elif not organization.domain:
        score -= float(rules.get("missing_website_penalty", 0))
        reasons.append("Apollo returned no website domain.")
    if organization.employee_count is not None:
        if (not icp.employee_min or organization.employee_count >= icp.employee_min) and (not icp.employee_max or organization.employee_count <= icp.employee_max):
            score += float(rules["employee_range_match"])
            reasons.append("Employee count matched the configured range.")
    negatives = [item.lower() for item in (icp.negative_keywords or icp.exclude_keywords) if item]
    matched_negatives = [item for item in negatives if item in content]
    score -= float(rules["negative_keyword_penalty"]) * len(matched_negatives)
    if matched_negatives:
        reasons.append(f"Negative keywords matched: {', '.join(matched_negatives)}.")
    unrelated = [str(item).lower() for item in rules.get("unrelated_business_keywords", []) if item]
    unrelated_matches = [item for item in unrelated if item in content]
    score -= float(rules.get("unrelated_business_penalty", 0)) * len(unrelated_matches)
    if unrelated_matches:
        reasons.append(f"Unrelated business signals matched: {', '.join(unrelated_matches)}.")
    threshold = float(rules["threshold"])
    band = confidence_band(score)
    return {
        "score": score,
        "threshold": threshold,
        "confidence_band": band,
        "passed": band != "Low Relevance",
        "status": "eligible" if band != "Low Relevance" else "filtered",
        "reasons": reasons,
        "matched_negative_keywords": matched_negatives,
        "matched_unrelated_keywords": unrelated_matches,
        "industry_normalization": {
            **industry_result,
            "industry_score_awarded": (
                float(rules["industry_match"])
                if industry_result["match_type"] == "exact"
                else float(rules["related_industry_family_match"])
                if industry_result["match_type"] == "related_family"
                else float(rules["manufacturing_family_match"])
                if industry_result["match_type"] == "manufacturing_family"
                else -float(rules["missing_industry_penalty"])
            ),
        },
        "strategy": strategy.to_metadata(),
    }
