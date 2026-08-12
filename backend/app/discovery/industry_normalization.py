from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from app.discovery.types import DiscoveryCompanyCandidate, ICPProductLine


@dataclass(frozen=True, slots=True)
class IndustryFamily:
    name: str
    apollo_industries: tuple[str, ...]
    related_sectors: tuple[str, ...]
    icp_profiles: tuple[str, ...]
    sic_prefixes: tuple[str, ...] = ()
    naics_prefixes: tuple[str, ...] = ()


INDUSTRY_FAMILIES = (
    IndustryFamily(
        name="metal_fabrication",
        apollo_industries=("metal fabrication", "welding & fabrication", "fabricators", "heavy engineering"),
        related_sectors=("machinery", "mechanical or industrial engineering", "industrial automation", "automotive", "aviation & aerospace"),
        icp_profiles=("metal fabrication", "welding & fabrication", "fabricators", "automotive manufacturing", "manufacturing plants"),
        sic_prefixes=("344", "346"),
        naics_prefixes=("3323", "3327", "3329"),
    ),
    IndustryFamily(
        name="industrial_manufacturing",
        apollo_industries=(
            "machinery", "mechanical or industrial engineering", "industrial automation",
            "industrial manufacturing", "manufacturing", "aviation & aerospace", "automotive",
            "semiconductors", "electronic manufacturing",
        ),
        related_sectors=("metal fabrication", "welding & fabrication", "fabrication", "machine builders"),
        icp_profiles=(
            "metal fabrication", "welding & fabrication", "precision engineering", "cnc job shops",
            "machine shops", "tool rooms", "machine builders", "industrial automation", "manufacturing plants",
            "automotive manufacturing", "automotive manufacturers", "electronics & ems", "jewellery manufacturing",
        ),
        sic_prefixes=("35", "36", "37", "38"),
        naics_prefixes=("31", "32", "33", "334", "335", "336"),
    ),
    IndustryFamily(
        name="electronics_and_semiconductors",
        apollo_industries=("semiconductors", "electronic manufacturing", "electronics manufacturing", "electrical/electronic manufacturing"),
        related_sectors=("industrial automation", "machinery", "automotive"),
        icp_profiles=("electronics & ems", "semiconductors", "industrial automation"),
        sic_prefixes=("367",),
        naics_prefixes=("3344", "334",),
    ),
)


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())).strip()


def _raw_record(organization: DiscoveryCompanyCandidate) -> dict[str, Any]:
    raw = organization.source_metadata.get("apollo_raw_record", organization.source_metadata)
    return raw if isinstance(raw, dict) else {}


def _values(organization: DiscoveryCompanyCandidate) -> tuple[list[str], list[str], list[str]]:
    raw = _raw_record(organization)
    industries = [organization.industry]
    raw_industries = raw.get("industries")
    if isinstance(raw_industries, list):
        industries.extend(raw_industries)
    elif raw_industries:
        industries.append(raw_industries)
    codes = []
    for key in ("sic_codes", "naics_codes"):
        value = raw.get(key) or []
        codes.extend(value if isinstance(value, list) else [value])
    supporting = [organization.name, organization.domain, organization.description]
    keywords = raw.get("keywords") or []
    supporting.extend(keywords if isinstance(keywords, list) else [keywords])
    return [_norm(item) for item in industries if item], [str(item).strip() for item in codes if item], [_norm(item) for item in supporting if item]


def _profile_relevant(family: IndustryFamily, icp: ICPProductLine) -> bool:
    labels = [icp.search_profile_name, icp.target_segment, *icp.exact_industries, *icp.related_industries, *icp.target_industries]
    normalized_labels = [_norm(label) for label in labels if label]
    return any(
        profile in label or label in profile
        for profile in family.icp_profiles
        for label in normalized_labels
    )


def normalize_industry(
    icp: ICPProductLine,
    organization: DiscoveryCompanyCandidate,
    *,
    exact_labels: list[str],
) -> dict[str, Any]:
    industries, codes, supporting = _values(organization)
    exact = [_norm(value) for value in exact_labels if value]
    exact_hit = next((value for value in industries if any(label and (label == value or label in value or value in label) for label in exact)), None)
    matched_family = None
    match_type = "none"
    matched_signal = exact_hit
    if exact_hit:
        match_type = "exact"
    else:
        for family in INDUSTRY_FAMILIES:
            if not _profile_relevant(family, icp):
                continue
            family_values = {_norm(item) for item in family.apollo_industries}
            related_values = {_norm(item) for item in family.related_sectors}
            code_hit = next((code for code in codes if any(code.startswith(prefix) for prefix in (*family.sic_prefixes, *family.naics_prefixes))), None)
            direct_hit = next((value for value in industries if value in family_values), None)
            related_hit = next((value for value in industries if value in related_values), None)
            if direct_hit or code_hit:
                matched_family = family
                match_type = "related_family" if direct_hit else "manufacturing_family"
                matched_signal = direct_hit or code_hit
                break
            if related_hit:
                matched_family = family
                match_type = "related_family"
                matched_signal = related_hit
                break
    return {
        "apollo_industry": organization.industry,
        "apollo_industries": industries,
        "sic_naics_codes": codes,
        "normalized_industry_family": matched_family.name if matched_family else None,
        "matched_icp_family": matched_family.name if matched_family and _profile_relevant(matched_family, icp) else None,
        "match_type": match_type,
        "matched_signal": matched_signal,
        "supporting_signals": supporting,
    }
