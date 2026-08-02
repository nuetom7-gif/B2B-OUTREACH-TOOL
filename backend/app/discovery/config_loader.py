from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.discovery.types import ICPProductLine


DEFAULT_ICP_PATH = Path(__file__).resolve().parents[1] / "config" / "icp.yml"


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


def _parse_product_line(payload: dict[str, Any]) -> ICPProductLine:
    return ICPProductLine(
        product_name=str(payload["product_name"]).strip(),
        enabled=bool(payload.get("enabled", True)),
        country=_as_list(payload.get("country")),
        regions=_as_list(payload.get("regions")),
        target_industries=_as_list(payload.get("target_industries")),
        exclude_industries=_as_list(payload.get("exclude_industries")),
        company_keywords=_as_list(payload.get("company_keywords")),
        exclude_keywords=_as_list(payload.get("exclude_keywords")),
        apollo_filters=_as_dict(payload.get("apollo_filters")),
        employee_min=int(payload.get("employee_min", 0) or 0),
        employee_max=int(payload.get("employee_max", 0) or 0),
        company_size=_as_list(payload.get("company_size")),
        preferred_company_types=_as_list(payload.get("preferred_company_types")),
        target_titles=_as_list(payload.get("target_titles")),
        preferred_titles=_as_list(payload.get("preferred_titles")),
        decision_level=_as_list(payload.get("decision_level")),
        lead_score_rules={str(key): value for key, value in _as_dict(payload.get("lead_score_rules")).items()},
        search_frequency=str(payload.get("search_frequency", "Daily")).strip(),
        priority=int(payload.get("priority", 0) or 0),
    )


@lru_cache
def load_icp_config(path: str | Path | None = None) -> list[ICPProductLine]:
    config_path = Path(path) if path else DEFAULT_ICP_PATH
    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    product_lines = payload.get("product_lines", [])
    return [_parse_product_line(item) for item in product_lines]

