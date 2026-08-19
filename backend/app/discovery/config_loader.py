from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.discovery.types import ICPProductLine


DEFAULT_ICP_PATH = Path(__file__).resolve().parents[1] / "config" / "icp.yml"
DEFAULT_PROFILE_DECISION_MAKERS = [
    "Purchase Manager", "Procurement Manager", "Purchase Head", "Procurement Head", "Sourcing Manager",
    "Plant Head", "Plant Manager", "Factory Manager", "Production Head", "Production Manager",
    "Operations Head", "Operations Manager", "Maintenance Head", "Maintenance Manager",
    "Engineering Head", "Engineering Manager", "EHS Manager", "Safety Manager", "Quality Manager",
    "Owner", "Founder", "Managing Director", "CEO", "Director", "General Manager",
]


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value).strip()]


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value or {})


def _decision_maker_titles(value: Any) -> tuple[list[str], dict[str, list[str]]]:
    if not isinstance(value, dict):
        return _as_list(value), {}
    tiers = {str(key): _as_list(items) for key, items in value.items()}
    flattened = []
    for titles in tiers.values():
        flattened.extend(titles)
    return list(dict.fromkeys(flattened)), tiers


def _parse_product_line(payload: dict[str, Any], *, base: dict[str, Any] | None = None) -> ICPProductLine:
    if base:
        merged = dict(base)
        merged.update(payload)
        payload = merged
    lead_score_rules = {str(key): value for key, value in _as_dict(payload.get("lead_score_rules")).items()}
    qualification_rules = {str(key): value for key, value in _as_dict(payload.get("qualification_rules")).items()}
    discovery_confidence_rules = {str(key): value for key, value in _as_dict(payload.get("discovery_confidence_rules")).items()}
    if payload.get("qualification") is not None:
        qualification_rules.update({str(key): value for key, value in _as_dict(payload.get("qualification")).items()})
    if qualification_rules:
        lead_score_rules = {**lead_score_rules, **qualification_rules}
    target_titles, decision_maker_tiers = _decision_maker_titles(
        payload.get("decision_maker_titles") or payload.get("decision_makers") or payload.get("target_titles")
    )
    apollo_industries = _as_list(payload.get("apollo_industries"))
    company_keywords = _as_list(payload.get("company_keywords"))
    # Hierarchical industry packs use the Apollo-facing names below, while
    # legacy micro-ICPs already use the normalized names. Keep one canonical
    # set so both configurations create identical search requests.
    product_keywords = _as_list(payload.get("product_keywords")) or company_keywords
    exact_industries = _as_list(payload.get("exact_industries")) or apollo_industries
    return ICPProductLine(
        product_name=str(payload["product_name"]).strip(),
        enabled=bool(payload.get("enabled", True)),
        country=_as_list(payload.get("country")),
        regions=_as_list(payload.get("regions")),
        target_industries=apollo_industries or _as_list(payload.get("target_industries")),
        exclude_industries=_as_list(payload.get("exclude_industries")),
        company_keywords=company_keywords,
        exclude_keywords=_as_list(payload.get("exclude_keywords")),
        apollo_filters=_as_dict(payload.get("apollo_filters")),
        employee_min=int(payload.get("employee_min", 0) or 0),
        employee_max=int(payload.get("employee_max", 0) or 0),
        company_size=_as_list(payload.get("company_size")),
        preferred_company_types=_as_list(payload.get("preferred_company_types")),
        target_titles=target_titles,
        preferred_titles=_as_list(payload.get("preferred_titles")),
        decision_level=_as_list(payload.get("decision_level")),
        lead_score_rules=lead_score_rules,
        search_frequency=str(payload.get("search_frequency", "Daily")).strip(),
        qualification_rules=qualification_rules,
        discovery_confidence_rules=discovery_confidence_rules,
        priority=int(payload.get("priority", 0) or 0),
        profile_name=str(payload.get("profile_name") or payload.get("name") or payload.get("micro_icp") or "").strip() or None,
        target_segment=str(payload.get("target_segment") or payload.get("name") or "").strip() or None,
        exact_industries=exact_industries,
        related_industries=_as_list(payload.get("related_industries")),
        broad_industries=_as_list(payload.get("broad_industries")),
        product_keywords=product_keywords,
        product_keyword_priorities={str(key): int(value) for key, value in _as_dict(payload.get("product_keyword_priorities")).items()},
        application_keywords=_as_list(payload.get("application_keywords")),
        manufacturing_keywords=_as_list(payload.get("manufacturing_keywords")),
        process_keywords=_as_list(payload.get("process_keywords")),
        negative_keywords=_as_list(payload.get("negative_keywords")),
        locations=_as_list(payload.get("locations")),
        apollo_search=_as_dict(payload.get("apollo_search")),
        business_division=str(payload.get("business_division") or "").strip() or None,
        states=_as_list(payload.get("states")),
        cities=_as_list(payload.get("cities")),
        apollo_industries=apollo_industries,
        decision_maker_tiers=decision_maker_tiers,
        manufacturing_cluster_preference=str(payload.get("manufacturing_cluster_preference") or "").strip() or None,
        product_recommendations=_as_list(payload.get("product_recommendations")),
        email_template_mapping=_as_dict(payload.get("email_template_mapping")),
        description=str(payload.get("description") or "").strip() or None,
        products=_as_list(payload.get("products")),
        portfolio_applications=_as_list(payload.get("portfolio_applications")),
    )


@lru_cache
def load_icp_config(path: str | Path | None = None) -> list[ICPProductLine]:
    config_path = Path(path) if path else DEFAULT_ICP_PATH
    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    hierarchical_profiles = payload.get("business_divisions") or []
    if hierarchical_profiles:
        global_defaults = _as_dict(payload.get("industry_pack_defaults"))
        result: list[ICPProductLine] = []
        for division in hierarchical_profiles:
            division_name = str(division.get("name") or division.get("business_division") or "").strip()
            division_defaults = _as_dict(division.get("defaults"))
            for pack in division.get("industry_packs", []) or []:
                merged = {**global_defaults, **division_defaults, **dict(pack)}
                merged["product_name"] = division_name
                merged["business_division"] = division_name
                merged["profile_name"] = str(pack.get("name") or pack.get("profile_name") or "").strip()
                result.append(_parse_product_line(merged))
        return result

    product_lines = payload.get("product_lines", [])
    bases = {str(item.get("product_name")): item for item in product_lines if isinstance(item, dict)}
    profiles = payload.get("micro_icps") or []
    if profiles:
        result = []
        for item in profiles:
            item = dict(item)
            product_name = str(item.get("product_name") or item.get("product_line") or "").strip()
            item.setdefault("target_titles", list(DEFAULT_PROFILE_DECISION_MAKERS))
            result.append(_parse_product_line(item, base=bases.get(product_name)))
        return result
    return [_parse_product_line(item) for item in product_lines]

