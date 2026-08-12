from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any


MISSING = object()
RAW_APOLLO_DIR = Path(__file__).resolve().parents[2] / "data" / "raw_apollo"


def save_raw_organization_json(*, run_id: int, organization_id: str, payload: dict[str, Any]) -> str:
    """Persist the complete Apollo response as one run-scoped JSON file."""
    safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", organization_id or "unknown")[:160]
    run_dir = RAW_APOLLO_DIR / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / f"organization_{safe_id}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return str(output_path)


def get_path(payload: Any, path: str) -> Any:
    value = payload
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return MISSING
        value = value[part]
    return value


def _has_value(value: Any) -> bool:
    return value is not MISSING and value not in (None, "", [])


def _walk_for_keys(payload: Any, aliases: set[str], path: str = "") -> tuple[str, Any] | None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            current_path = f"{path}.{key}" if path else str(key)
            if str(key).lower() in aliases and _has_value(value):
                return current_path, value
            found = _walk_for_keys(value, aliases, current_path)
            if found:
                return found
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            found = _walk_for_keys(value, aliases, f"{path}[{index}]")
            if found:
                return found
    return None


def resolve_field(payload: dict[str, Any], paths: list[str]) -> tuple[str | None, Any, bool]:
    """Resolve a field from preferred paths, then recursively search aliases."""
    for path in paths:
        value = get_path(payload, path)
        if _has_value(value):
            return path, value, False
    aliases = {path.rsplit(".", 1)[-1].lower() for path in paths}
    found = _walk_for_keys(payload, aliases)
    if found:
        return found[0], found[1], True
    return None, None, False


def mapping_entry(payload: dict[str, Any], paths: list[str], value: Any) -> dict[str, Any]:
    selected, source_value, fallback_used = resolve_field(payload, paths)
    present = [path for path in paths if get_path(payload, path) is not MISSING]
    missing_reason = None
    if value in (None, "", []):
        missing_reason = f"No value found at attempted paths or recursive aliases: {', '.join(paths)}"
    return {
        "json_path_attempted": selected or paths[0],
        "alternate_paths_checked": paths,
        "field_exists_elsewhere": bool(fallback_used),
        "paths_present": present + ([selected] if selected and selected not in present else []),
        "source_value_at_selected_path": source_value,
        "extracted_value": value,
        "fallback_used": fallback_used,
        "confidence": "high" if selected and not fallback_used else "medium" if selected else "missing",
        "why_unknown": missing_reason,
    }


ORGANIZATION_PATHS = {
    "Company Name": ["name", "organization_name", "company_name", "organization.name", "account.name"],
    "Country": [
        "organization_location.country", "organization_location.country_name", "location.country",
        "organization.country", "address.country", "country",
    ],
    "Region": [
        "organization_location.state", "organization_location.region", "location.state",
        "location.region", "organization.state", "region",
    ],
    "City": [
        "organization_location.city", "location.city", "organization.city", "address.city", "city",
    ],
    "Industry": [
        "industry", "primary_industry", "organization_industry", "organization.primary_industry",
        "organization.industry", "industries",
    ],
    "Employee Count": [
        "estimated_num_employees", "organization_num_employees", "organization.estimated_num_employees",
        "employees", "employee_count", "organization.employee_count",
    ],
    "Description": [
        "short_description", "description", "headline", "organization_summary", "summary",
        "organization.short_description", "organization.description",
    ],
    "Website": [
        "primary_domain", "domain", "website_url", "website", "organization.website_url",
        "organization.domain",
    ],
    "LinkedIn": ["linkedin_url", "linkedin_url_normalized", "organization.linkedin_url"],
    "Revenue": [
        "annual_revenue", "estimated_annual_revenue", "revenue", "organization.annual_revenue",
        "organization.estimated_annual_revenue",
    ],
    "Technologies": ["technologies", "technology_names", "organization.technologies"],
}


def extract_organization_fields(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    values: dict[str, Any] = {}
    mapping: dict[str, Any] = {}
    for field, paths in ORGANIZATION_PATHS.items():
        selected, raw_value, fallback_used = resolve_field(item, paths)
        if field == "Industry" and isinstance(raw_value, list):
            raw_value = ", ".join(str(value) for value in raw_value if value)
        values[field] = raw_value
        mapping[field] = mapping_entry(item, paths, raw_value)
    return values, mapping


def _leaf_paths(payload: Any, path: str = "") -> list[str]:
    if isinstance(payload, dict):
        result: list[str] = []
        for key, value in payload.items():
            current_path = f"{path}.{key}" if path else str(key)
            result.extend(_leaf_paths(value, current_path))
        return result
    if isinstance(payload, list):
        result = []
        for index, value in enumerate(payload):
            result.extend(_leaf_paths(value, f"{path}[{index}]"))
        return result
    return [path]


def unused_organization_fields(item: dict[str, Any], mapping: dict[str, Any]) -> list[str]:
    used = {
        str(entry.get("json_path_attempted"))
        for entry in mapping.values()
        if entry.get("confidence") != "missing"
    }
    return [
        path for path in _leaf_paths(item)
        if not any(path == selected or path.startswith(f"{selected}.") for selected in used)
    ]


def organization_field_mapping(item: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    _, mapping = extract_organization_fields(item)
    return mapping


def people_field_mapping(item: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "Contact Name": ["name", "first_name + last_name"],
        "Title": ["title", "job_title"],
        "Email": ["email", "work_email", "contact_email"],
        "Phone": ["phone", "mobile_phone"],
        "LinkedIn": ["linkedin_url", "linkedin_url_normalized"],
        "Email Status": ["email_status", "contact_email_status"],
        "Country": ["country"],
        "Region": ["region"],
    }
    normalized_fields = {
        "Contact Name": normalized.get("name"),
        "Title": normalized.get("title"),
        "Email": normalized.get("email"),
        "Phone": normalized.get("phone"),
        "LinkedIn": normalized.get("linkedin_url"),
        "Email Status": normalized.get("email_status"),
        "Country": normalized.get("country"),
        "Region": normalized.get("region"),
    }
    return {
        field: mapping_entry(item, candidate_paths, normalized_fields[field])
        for field, candidate_paths in paths.items()
    }
