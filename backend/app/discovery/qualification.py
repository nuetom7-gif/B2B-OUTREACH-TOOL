from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.discovery.types import (
    DiscoveryCompanyCandidate,
    DiscoveryContactCandidate,
    DiscoveryScoreResult,
    ICPProductLine,
    QualificationImpact,
    QualificationRuleResult,
)


DEFAULT_BROAD_INDUSTRY_TERMS = [
    "manufacturing",
    "factory",
    "industrial",
    "engineering",
    "production",
    "processing",
]

DEFAULT_VERIFIED_EMAIL_POINTS = 3.0
DEFAULT_QUALIFICATION_THRESHOLD = 70.0
DEFAULT_MANUAL_REVIEW_THRESHOLD = 45.0


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _contains_any(haystack: str | None, needles: list[str]) -> bool:
    lowered = _normalize_text(haystack)
    if not lowered:
        return False
    return any(_normalize_text(needle) in lowered for needle in needles if _normalize_text(needle))


def _first_match(haystack: str | None, needles: list[str]) -> str | None:
    lowered = _normalize_text(haystack)
    if not lowered:
        return None
    for needle in needles:
        candidate = _normalize_text(needle)
        if candidate and candidate in lowered:
            return needle
    return None


def _rules(icp: ICPProductLine) -> dict[str, Any]:
    merged = dict(icp.lead_score_rules)
    merged.update(icp.qualification_rules or {})
    return merged


def _section(rules: dict[str, Any], *names: str) -> dict[str, Any]:
    for name in names:
        value = rules.get(name)
        if isinstance(value, dict):
            return value
    return {}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value).strip()]


def _weight_map(value: Any, *, default_points: float | None = None) -> dict[str, float]:
    if not value:
        return {}
    weights: dict[str, float] = {}
    if isinstance(value, dict):
        for key, raw_points in value.items():
            if key is None:
                continue
            points = _as_float(raw_points, default_points or 0.0)
            weights[str(key).strip()] = points
        return weights
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                label = str(
                    item.get("label")
                    or item.get("name")
                    or item.get("term")
                    or item.get("title")
                    or item.get("city")
                    or item.get("keyword")
                    or ""
                ).strip()
                if not label:
                    continue
                points = _as_float(item.get("points") or item.get("score") or item.get("value"), default_points or 0.0)
                weights[label] = points
            else:
                label = str(item).strip()
                if label:
                    weights[label] = float(default_points or 0.0)
        return weights
    label = str(value).strip()
    if label:
        weights[label] = float(default_points or 0.0)
    return weights


def _score_sum(matches: list[tuple[str, float]]) -> float:
    return sum(points for _, points in matches)


def _find_weighted_matches(texts: list[str | None], weights: dict[str, float]) -> list[tuple[str, float]]:
    matches: list[tuple[str, float]] = []
    seen: set[str] = set()
    lowered_texts = [_normalize_text(text) for text in texts if _normalize_text(text)]
    for label, points in weights.items():
        normalized_label = _normalize_text(label)
        if not normalized_label or normalized_label in seen:
            continue
        if any(normalized_label in text for text in lowered_texts):
            matches.append((label, float(points)))
            seen.add(normalized_label)
    return matches


def _first_positive_match(texts: list[str | None], weights: dict[str, float]) -> tuple[str | None, float]:
    matches = _find_weighted_matches(texts, weights)
    positives = [(label, points) for label, points in matches if points > 0]
    if not positives:
        return None, 0.0
    return max(positives, key=lambda item: item[1])


def _record_rule(name: str, points_awarded: float, max_points: float, reason: str) -> QualificationRuleResult:
    return QualificationRuleResult(
        rule_name=name,
        passed=points_awarded > 0,
        points_awarded=points_awarded,
        max_points=max_points,
        reason=reason,
    )


def _confidence_for_result(status: str, score: float, qualification_threshold: float, matched_industry_level: str | None) -> str:
    if status == "qualified":
        if matched_industry_level == "exact" and score >= qualification_threshold + 10:
            return "High"
        return "High" if score >= qualification_threshold + 15 else "Medium"
    if status == "manual_review":
        return "Medium"
    return "Low"


def _industry_rules(
    rules: dict[str, Any],
    icp: ICPProductLine,
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    industry = _section(rules, "industry", "industry_rules")
    exact = _weight_map(
        industry.get("exact_industries")
        or industry.get("exact")
        or rules.get("exact_industries")
        or rules.get("target_industries")
        or icp.target_industries
        or [],
        default_points=_as_float(rules.get("exact_industry_points"), _as_float(rules.get("industry_match"), 45.0)),
    )
    related = _weight_map(
        industry.get("related_industries") or industry.get("related") or rules.get("related_industries") or icp.preferred_company_types or [],
        default_points=_as_float(rules.get("related_industry_points"), 25.0),
    )
    broad = _weight_map(
        industry.get("broad_industries")
        or industry.get("broad")
        or rules.get("broad_industries")
        or rules.get("broad_industry_terms")
        or icp.company_keywords
        or DEFAULT_BROAD_INDUSTRY_TERMS,
        default_points=_as_float(rules.get("broad_industry_points"), 10.0),
    )
    return exact, related, broad


def _keyword_rules(rules: dict[str, Any], icp: ICPProductLine) -> dict[str, dict[str, float]]:
    keyword = _section(rules, "keywords", "keyword_rules")
    return {
        "product": _weight_map(
            keyword.get("product_keywords")
            or keyword.get("product")
            or rules.get("product_keywords")
            or rules.get("company_keywords")
            or icp.company_keywords
            or [],
            default_points=_as_float(rules.get("product_keyword_points"), 12.0),
        ),
        "manufacturing": _weight_map(
            keyword.get("manufacturing_keywords")
            or keyword.get("manufacturing")
            or rules.get("manufacturing_keywords")
            or icp.company_keywords
            or [],
            default_points=_as_float(rules.get("manufacturing_keyword_points"), 8.0),
        ),
        "process": _weight_map(
            keyword.get("process_keywords")
            or keyword.get("process")
            or rules.get("process_keywords")
            or [],
            default_points=_as_float(rules.get("process_keyword_points"), 6.0),
        ),
    }


def _negative_rules(rules: dict[str, Any], icp: ICPProductLine) -> dict[str, float]:
    negative = _section(rules, "negative_keywords", "negative_signals")
    negatives = negative or rules.get("negative_keywords") or rules.get("exclude_keywords") or icp.exclude_keywords or []
    weights = _weight_map(negatives, default_points=0.0)
    normalized: dict[str, float] = {}
    for label, points in weights.items():
        normalized[label] = -abs(points if points else _as_float(rules.get("negative_keyword_penalty"), 8.0))
    return normalized


def _employee_bands(rules: dict[str, Any], icp: ICPProductLine) -> list[dict[str, Any]]:
    employee = _section(rules, "employee", "employee_scoring")
    bands = employee.get("employee_range_scores") or rules.get("employee_range_scores") or []
    result: list[dict[str, Any]] = []
    if isinstance(bands, list):
        for item in bands:
            if not isinstance(item, dict):
                continue
            result.append(
                {
                    "label": str(item.get("label") or item.get("name") or f"{item.get('min', 0)}-{item.get('max', 0)}").strip(),
                    "min": item.get("min"),
                    "max": item.get("max"),
                    "points": _as_float(item.get("points") or item.get("score"), 0.0),
                }
            )
    if not result and (icp.employee_min or icp.employee_max):
        result = [
            {
                "label": f"{icp.employee_min}-{icp.employee_max}" if icp.employee_max else f"{icp.employee_min}+",
                "min": icp.employee_min or 0,
                "max": icp.employee_max or None,
                "points": _as_float(rules.get("company_size_fit") or rules.get("company_size_points"), 10.0),
            }
        ]
    return result


def _country_rules(rules: dict[str, Any], icp: ICPProductLine) -> dict[str, Any]:
    country = _section(rules, "country", "country_rules")
    allowed = country.get("allowed") or country.get("countries") or rules.get("country") or icp.country or []
    return {
        "allowed": _as_list(allowed),
        "points": _as_float(country.get("points") or rules.get("country_match_points"), 10.0),
        "penalty": _as_float(country.get("penalty") or rules.get("country_mismatch_penalty"), 0.0),
    }


def _thresholds(rules: dict[str, Any]) -> tuple[float, float]:
    thresholds = _section(rules, "thresholds", "qualification_thresholds")
    qualification = _as_float(
        thresholds.get("qualification") or thresholds.get("qualified") or rules.get("qualification_threshold") or rules.get("import_threshold"),
        DEFAULT_QUALIFICATION_THRESHOLD,
    )
    manual_review = _as_float(
        thresholds.get("manual_review") or rules.get("manual_review_threshold"),
        min(qualification, DEFAULT_MANUAL_REVIEW_THRESHOLD),
    )
    return qualification, manual_review


def _verified_points(rules: dict[str, Any]) -> float:
    verified = _section(rules, "verified_email", "email_verification", "verified_contact")
    return _as_float(
        verified.get("points")
        or rules.get("verified_email_points")
        or rules.get("verified_contact_points")
        or rules.get("verified_contact_present"),
        DEFAULT_VERIFIED_EMAIL_POINTS,
    )


def _cluster_rules(rules: dict[str, Any]) -> dict[str, float]:
    clusters = _section(rules, "manufacturing_clusters", "clusters")
    cluster_map = clusters or rules.get("manufacturing_clusters") or []
    return _weight_map(cluster_map, default_points=3.0)


def _decision_maker_rules(rules: dict[str, Any], icp: ICPProductLine) -> dict[str, float]:
    decision = _section(rules, "decision_maker_scores", "decision_makers")
    return _weight_map(
        decision or rules.get("decision_maker_scores") or rules.get("target_titles") or icp.target_titles + icp.preferred_titles or [],
        default_points=_as_float(rules.get("decision_maker_found"), 25.0),
    )


def _location_hints(organization: DiscoveryCompanyCandidate) -> list[str]:
    hints = [organization.city, organization.region, organization.country]
    payload = organization.source_metadata or {}
    for key in ("city", "city_name", "locality", "metro_area", "headquarters_city", "hq_city", "location_city"):
        value = payload.get(key)
        if value:
            hints.append(str(value))
    if isinstance(payload.get("location"), dict):
        location = payload["location"]
        for key in ("city", "locality", "metro_area", "town", "region", "state"):
            value = location.get(key)
            if value:
                hints.append(str(value))
    return [hint for hint in hints if hint and str(hint).strip()]


def _is_missing_organization_data(organization: DiscoveryCompanyCandidate) -> bool:
    return not organization.name or not (organization.industry or organization.description or organization.company_size)


def _is_missing_person_data(person: DiscoveryContactCandidate) -> bool:
    return not person.name or not person.title


def _summarize_impacts(impacts: list[QualificationImpact]) -> list[dict[str, Any]]:
    return [
        {
            "label": impact.label,
            "category": impact.category,
            "points": impact.points,
            "reason": impact.reason,
            "matched_value": impact.matched_value,
        }
        for impact in impacts
    ]


def _score_organization_rule_set(
    icp: ICPProductLine,
    organization: DiscoveryCompanyCandidate,
    people: list[DiscoveryContactCandidate],
) -> dict[str, Any]:
    rules = _rules(icp)
    score = 0.0
    rule_results: list[QualificationRuleResult] = []
    applied_bonuses: list[QualificationImpact] = []
    applied_penalties: list[QualificationImpact] = []
    matched_keywords: list[str] = []
    matched_keyword_groups: list[str] = []
    matched_industry_level: str | None = None
    matched_industry_name: str | None = None
    matched_decision_maker_title: str | None = None
    matched_cluster: str | None = None

    country_rules = _country_rules(rules, icp)
    country_points = 0.0
    if country_rules["allowed"]:
        if organization.country and organization.country in country_rules["allowed"]:
            country_points = country_rules["points"]
            applied_bonuses.append(
                QualificationImpact(
                    label="Country Match",
                    category="country",
                    points=country_points,
                    reason=f"Country matched configured target country: {organization.country}.",
                    matched_value=organization.country,
                )
            )
        else:
            if organization.country:
                country_points = -country_rules["penalty"] if country_rules["penalty"] > 0 else 0.0
                if country_points:
                    applied_penalties.append(
                        QualificationImpact(
                            label="Country Mismatch",
                            category="country",
                            points=country_points,
                            reason=f"Country '{organization.country}' did not match configured countries: {', '.join(country_rules['allowed'])}.",
                            matched_value=organization.country,
                        )
                    )
    score += country_points
    rule_results.append(
        _record_rule(
            "Country",
            country_points,
            country_rules["points"],
            (
                f"Matched country: {organization.country}."
                if country_points > 0
                else f"Country '{organization.country or 'unknown'}' did not match configured countries."
            ),
        )
    )

    exact_industries, related_industries, broad_industries = _industry_rules(rules, icp)
    industry_candidates = [organization.industry, organization.name, organization.description]
    industry_score = 0.0
    industry_max = 0.0
    industry_reason = f"Industry '{organization.industry or 'unknown'}' did not match configured industry signals."

    for level, weights in (
        ("exact", exact_industries),
        ("related", related_industries),
        ("broad", broad_industries),
    ):
        if not weights:
            continue
        industry_max = max(industry_max, max(weights.values()) if weights else 0.0)
        label, points = _first_positive_match(industry_candidates, weights)
        if label:
            matched_industry_level = level
            matched_industry_name = label
            industry_score = points
            industry_reason = f"Matched {level} industry: {label}."
            applied_bonuses.append(
                QualificationImpact(
                    label=f"Industry {level.title()} Match",
                    category="industry",
                    points=points,
                    reason=industry_reason,
                    matched_value=label,
                )
            )
            break
    score += industry_score
    rule_results.append(_record_rule("Industry Match", industry_score, industry_max, industry_reason))

    keyword_rules = _keyword_rules(rules, icp)
    keyword_rule_labels = {
        "product": "Product Keywords",
        "manufacturing": "Manufacturing Keywords",
        "process": "Process Keywords",
    }
    keyword_max_map = {
        "product": sum(keyword_rules["product"].values()),
        "manufacturing": sum(keyword_rules["manufacturing"].values()),
        "process": sum(keyword_rules["process"].values()),
    }
    for group_name, weights in keyword_rules.items():
        matches = _find_weighted_matches(industry_candidates, weights)
        points = _score_sum(matches)
        labels = [label for label, _ in matches]
        if labels:
            matched_keyword_groups.append(group_name)
            matched_keywords.extend(labels)
            applied_bonuses.extend(
                QualificationImpact(
                    label=f"{keyword_rule_labels[group_name][:-1]}: {label}",
                    category=f"keyword:{group_name}",
                    points=points,
                    reason=f"Matched {group_name} keyword '{label}'.",
                    matched_value=label,
                )
                for label, _points in matches
            )
        score += points
        reason = (
            f"Matched {group_name} keywords: {', '.join(labels)}."
            if labels
            else f"No {group_name} keywords matched."
        )
        rule_results.append(_record_rule(keyword_rule_labels[group_name], points, keyword_max_map[group_name], reason))

    employee_bands = _employee_bands(rules, icp)
    employee_points = 0.0
    employee_reason = "Employee count unavailable from Apollo."
    employee_max = max((band["points"] for band in employee_bands), default=0.0)
    if organization.employee_count is not None and employee_bands:
        for band in employee_bands:
            min_value = _as_int(band.get("min"), 0)
            max_value = band.get("max")
            max_value = None if max_value in (None, "", "null") else _as_int(max_value, 0)
            if organization.employee_count >= min_value and (max_value is None or organization.employee_count <= max_value):
                employee_points = _as_float(band.get("points"), 0.0)
                band_label = band.get("label") or f"{min_value}-{max_value or 'plus'}"
                employee_reason = (
                    f"Employee count {organization.employee_count} matched band {band_label}."
                )
                applied_bonuses.append(
                    QualificationImpact(
                        label="Employee Band",
                        category="employee",
                        points=employee_points,
                        reason=employee_reason,
                        matched_value=band_label,
                    )
                )
                break
        else:
            employee_reason = f"Employee count {organization.employee_count} did not match any configured band."
    score += employee_points
    rule_results.append(_record_rule("Employee Count", employee_points, employee_max, employee_reason))

    decision_maker_rules = _decision_maker_rules(rules, icp)
    decision_maker_points = 0.0
    decision_maker_reason = "No configured decision maker was found."
    decision_maker_max = max(decision_maker_rules.values(), default=0.0)
    for person in people:
        title = person.title or ""
        label, points = _first_positive_match([title], decision_maker_rules)
        if label and points > 0:
            if points >= decision_maker_points:
                decision_maker_points = points
                matched_decision_maker_title = label
                decision_maker_reason = f"Found decision maker title '{title}' matching '{label}'."
    if decision_maker_points > 0:
        applied_bonuses.append(
            QualificationImpact(
                label="Decision Maker",
                category="decision_maker",
                points=decision_maker_points,
                reason=decision_maker_reason,
                matched_value=matched_decision_maker_title,
            )
        )
    score += decision_maker_points
    rule_results.append(_record_rule("Decision Maker", decision_maker_points, decision_maker_max, decision_maker_reason))

    verified_points = _verified_points(rules)
    verified_contact_present = any((person.email_status or "").lower() == "verified" for person in people)
    verified_score = verified_points if verified_contact_present else 0.0
    if verified_score > 0:
        applied_bonuses.append(
            QualificationImpact(
                label="Verified Email",
                category="email",
                points=verified_score,
                reason="At least one Apollo email was verified.",
                matched_value="verified",
            )
        )
    score += verified_score
    rule_results.append(_record_rule("Verified Email", verified_score, verified_points, "At least one Apollo email was verified." if verified_score > 0 else "No verified email found."))

    cluster_rules = _cluster_rules(rules)
    cluster_score = 0.0
    cluster_reason = "No manufacturing cluster matched."
    location_hints = _location_hints(organization)
    matched_cluster_weights = _find_weighted_matches(location_hints, cluster_rules)
    if matched_cluster_weights:
        matched_cluster, cluster_score = max(matched_cluster_weights, key=lambda item: item[1])
        cluster_reason = f"Matched manufacturing cluster: {matched_cluster}."
        applied_bonuses.append(
            QualificationImpact(
                label="Manufacturing Cluster",
                category="cluster",
                points=cluster_score,
                reason=cluster_reason,
                matched_value=matched_cluster,
            )
        )
    score += cluster_score
    rule_results.append(_record_rule("Manufacturing Cluster", cluster_score, max(cluster_rules.values(), default=0.0), cluster_reason))

    negative_rules = _negative_rules(rules, icp)
    negative_matches = _find_weighted_matches(industry_candidates + location_hints, negative_rules)
    negative_score = _score_sum(negative_matches)
    if negative_matches:
        for label, points in negative_matches:
            applied_penalties.append(
                QualificationImpact(
                    label=f"Negative Signal: {label}",
                    category="penalty",
                    points=points,
                    reason=f"Matched negative signal '{label}'.",
                    matched_value=label,
                )
            )
    score += negative_score
    negative_reason = (
        f"Applied penalties for: {', '.join(label for label, _ in negative_matches)}."
        if negative_matches
        else "No negative signals matched."
    )
    rule_results.append(_record_rule("Negative Signals", negative_score, 0.0, negative_reason))

    missing_data = _is_missing_organization_data(organization)
    qualification_threshold, manual_review_threshold = _thresholds(rules)

    positive_signal = bool(matched_industry_level or matched_keywords or matched_decision_maker_title or cluster_score > 0)
    strong_industry = matched_industry_level in {"exact", "related", "broad"}
    strong_exact_match = matched_industry_level == "exact"
    has_decent_employee_band = employee_points > 0

    if score >= qualification_threshold and strong_industry and matched_decision_maker_title:
        status = "qualified"
    elif score >= manual_review_threshold or missing_data or positive_signal or has_decent_employee_band:
        status = "manual_review"
    else:
        status = "rejected"

    final_confidence = _confidence_for_result(status, score, qualification_threshold, matched_industry_level)
    reasons = [rule.reason for rule in rule_results if rule.points_awarded <= 0 and rule.reason]

    return {
        "score": score,
        "status": status,
        "needs_manual_review": status == "manual_review",
        "reasons": reasons,
        "matched_industry": bool(matched_industry_level),
        "matched_industry_level": matched_industry_level,
        "matched_industry_name": matched_industry_name,
        "matched_keyword": bool(matched_keywords),
        "matched_keywords": sorted(dict.fromkeys(matched_keywords)),
        "matched_keyword_groups": sorted(dict.fromkeys(matched_keyword_groups)),
        "matched_company_size": employee_points > 0,
        "matched_decision_maker": bool(matched_decision_maker_title),
        "matched_decision_maker_title": matched_decision_maker_title,
        "verified_contact_present": verified_contact_present,
        "applied_bonuses": applied_bonuses,
        "applied_penalties": applied_penalties,
        "qualification_threshold": qualification_threshold,
        "manual_review_threshold": manual_review_threshold,
        "evaluation_timestamp": datetime.now(timezone.utc),
        "rule_results": rule_results,
        "overall_recommendation": status.replace("_", " ").title(),
        "final_confidence": final_confidence,
        "matched_cluster": matched_cluster,
    }


def score_organization(
    icp: ICPProductLine,
    organization: DiscoveryCompanyCandidate,
    people: list[DiscoveryContactCandidate],
) -> DiscoveryScoreResult:
    payload = _score_organization_rule_set(icp, organization, people)
    return DiscoveryScoreResult(**payload)


def score_person(icp: ICPProductLine, person: DiscoveryContactCandidate) -> DiscoveryScoreResult:
    rules = _rules(icp)
    score = 0.0
    rule_results: list[QualificationRuleResult] = []
    applied_bonuses: list[QualificationImpact] = []
    applied_penalties: list[QualificationImpact] = []

    decision_maker_rules = _decision_maker_rules(rules, icp)
    decision_maker_max = max(decision_maker_rules.values(), default=0.0)
    title = person.title or ""
    matched_title, decision_points = _first_positive_match([title], decision_maker_rules)
    decision_reason = "No configured decision maker was found."
    if matched_title and decision_points > 0:
        decision_reason = f"Matched decision maker title '{title}' as '{matched_title}'."
        applied_bonuses.append(
            QualificationImpact(
                label="Decision Maker",
                category="decision_maker",
                points=decision_points,
                reason=decision_reason,
                matched_value=matched_title,
            )
        )
        score += decision_points
    rule_results.append(_record_rule("Decision Maker", decision_points, decision_maker_max, decision_reason))

    verified_points = _verified_points(rules)
    verified_contact_present = (person.email_status or "").lower() == "verified"
    verified_score = verified_points if verified_contact_present else 0.0
    if verified_score > 0:
        applied_bonuses.append(
            QualificationImpact(
                label="Verified Email",
                category="email",
                points=verified_score,
                reason="Contact email was Apollo-verified.",
                matched_value="verified",
            )
        )
        score += verified_score
    rule_results.append(_record_rule("Verified Email", verified_score, verified_points, "Contact email was Apollo-verified." if verified_score > 0 else "No verified email found."))

    qualification_threshold, manual_review_threshold = _thresholds(rules)
    missing_data = _is_missing_person_data(person)

    positive_signal = bool(matched_title or verified_contact_present)
    if score >= qualification_threshold and matched_title:
        status = "qualified"
    elif score >= manual_review_threshold or missing_data or positive_signal:
        status = "manual_review"
    else:
        status = "rejected"

    final_confidence = _confidence_for_result(status, score, qualification_threshold, "exact" if matched_title else None)
    reasons = [rule.reason for rule in rule_results if rule.points_awarded <= 0 and rule.reason]

    return DiscoveryScoreResult(
        score=score,
        status=status,
        needs_manual_review=status == "manual_review",
        reasons=reasons,
        matched_industry=False,
        matched_industry_level=None,
        matched_industry_name=None,
        matched_keyword=bool(matched_title),
        matched_keywords=[matched_title] if matched_title else [],
        matched_keyword_groups=["decision_maker"] if matched_title else [],
        matched_company_size=False,
        matched_decision_maker=bool(matched_title),
        matched_decision_maker_title=matched_title,
        verified_contact_present=verified_contact_present,
        applied_bonuses=applied_bonuses,
        applied_penalties=applied_penalties,
        qualification_threshold=qualification_threshold,
        manual_review_threshold=manual_review_threshold,
        evaluation_timestamp=datetime.now(timezone.utc),
        rule_results=rule_results,
        overall_recommendation=status.replace("_", " ").title(),
        final_confidence=final_confidence,
        matched_cluster=None,
    )


def summarize_qualification_results(
    results: list[DiscoveryScoreResult],
    *,
    product_name: str,
    run_id: int,
    imported_count: int = 0,
) -> dict[str, Any]:
    status_counter = Counter(result.status for result in results)
    failure_counter = Counter()
    bonus_counter = Counter()
    penalty_counter = Counter()
    industry_counter = Counter()
    keyword_counter = Counter()
    cluster_counter = Counter()
    decision_counter = Counter()
    scores: list[float] = []

    for result in results:
        scores.append(float(result.score))
        for rule in result.rule_results:
            if rule.points_awarded <= 0 and rule.reason:
                failure_counter[rule.rule_name] += 1
        for bonus in result.applied_bonuses:
            bonus_counter[bonus.label] += 1
            if bonus.category == "industry":
                industry_counter[bonus.matched_value or bonus.label] += 1
            if bonus.category.startswith("keyword:") and bonus.matched_value:
                keyword_counter[bonus.matched_value] += 1
            if bonus.category == "cluster" and bonus.matched_value:
                cluster_counter[bonus.matched_value] += 1
            if bonus.category == "decision_maker" and bonus.matched_value:
                decision_counter[bonus.matched_value] += 1
            if bonus.category == "keyword:product" and bonus.matched_value:
                keyword_counter[bonus.matched_value] += 1
        for penalty in result.applied_penalties:
            penalty_counter[penalty.label] += 1

        if result.matched_industry_name:
            industry_counter[result.matched_industry_name] += 1
        for keyword in result.matched_keywords:
            keyword_counter[keyword] += 1
        if result.matched_cluster:
            cluster_counter[result.matched_cluster] += 1
        if result.matched_decision_maker_title:
            decision_counter[result.matched_decision_maker_title] += 1

    average_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    return {
        "run_id": run_id,
        "product_name": product_name,
        "companies_evaluated": len(results),
        "qualified": status_counter.get("qualified", 0),
        "manual_review": status_counter.get("manual_review", 0),
        "rejected": status_counter.get("rejected", 0),
        "imported": imported_count,
        "average_score": average_score,
        "most_common_failure_reasons": [{"label": label, "count": count} for label, count in failure_counter.most_common(10)],
        "most_common_bonuses": [{"label": label, "count": count} for label, count in bonus_counter.most_common(10)],
        "most_common_penalties": [{"label": label, "count": count} for label, count in penalty_counter.most_common(10)],
        "most_matched_industries": [{"label": label, "count": count} for label, count in industry_counter.most_common(10)],
        "most_matched_keywords": [{"label": label, "count": count} for label, count in keyword_counter.most_common(15)],
        "top_manufacturing_clusters": [{"label": label, "count": count} for label, count in cluster_counter.most_common(10)],
        "top_decision_maker_titles": [{"label": label, "count": count} for label, count in decision_counter.most_common(10)],
        "average_score_per_icp": {product_name: average_score},
        "average_score_per_product_line": {product_name: average_score},
    }
