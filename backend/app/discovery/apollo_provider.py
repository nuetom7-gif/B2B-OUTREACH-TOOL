from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.discovery.provider import DiscoveryProvider
from app.discovery.types import DiscoveryCompanyCandidate, DiscoveryContactCandidate, ICPProductLine


class ApolloProviderError(RuntimeError):
    pass


class ApolloRateLimitError(ApolloProviderError):
    pass


class ApolloProvider(DiscoveryProvider):
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = httpx.Client(
            base_url=self.settings.apollo_base_url.rstrip("/"),
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.settings.apollo_api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        self._last_call_monotonic = 0.0

    def provider_name(self) -> str:
        return "apollo"

    def close(self) -> None:
        self._client.close()

    def _sleep_if_needed(self) -> None:
        minimum = max(0.0, float(self.settings.apollo_min_seconds_between_calls))
        elapsed = time.monotonic() - self._last_call_monotonic
        if self._last_call_monotonic and elapsed < minimum:
            time.sleep(minimum - elapsed)

    def _request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.settings.apollo_api_key.strip():
            raise ApolloProviderError("APOLLO_API_KEY is not configured")
        self._sleep_if_needed()
        response = None
        for attempt in range(max(1, self.settings.apollo_retry_limit)):
            try:
                response = self._client.request(method, path, params=params, json=json)
                self._last_call_monotonic = time.monotonic()
                if response.status_code == 429:
                    if attempt + 1 >= self.settings.apollo_retry_limit:
                        raise ApolloRateLimitError("Apollo rate limit reached")
                    time.sleep(2**attempt)
                    continue
                if response.status_code in (401, 403):
                    raise ApolloProviderError(f"Apollo authentication or permission error: {response.text}")
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, dict):
                    return payload
                return {"results": payload}
            except httpx.HTTPError as exc:
                if attempt + 1 >= self.settings.apollo_retry_limit:
                    raise ApolloProviderError(f"Apollo request failed: {exc}") from exc
                time.sleep(2**attempt)
        raise ApolloProviderError("Apollo request failed unexpectedly")

    def _employee_ranges(self, icp: ICPProductLine) -> list[str]:
        if icp.employee_min <= 0 and icp.employee_max <= 0:
            return []
        return [f"{max(1, icp.employee_min)},{max(icp.employee_min, icp.employee_max)}"]

    def _common_org_params(self, icp: ICPProductLine, *, page: int, per_page: int) -> dict[str, Any]:
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }
        if icp.country:
            params["organization_locations[]"] = icp.country
        ranges = self._employee_ranges(icp)
        if ranges:
            params["organization_num_employees_ranges[]"] = ranges
        keyword_tags = list(dict.fromkeys(icp.target_industries + icp.company_keywords))
        if keyword_tags:
            params["q_organization_keyword_tags[]"] = keyword_tags
        if icp.exclude_keywords:
            params["q_organization_name"] = None
        return params

    def search_organizations(self, icp: ICPProductLine, *, page: int, per_page: int) -> list[DiscoveryCompanyCandidate]:
        payload = self._request(
            "POST",
            "/mixed_companies/search",
            params=self._common_org_params(icp, page=page, per_page=per_page),
        )
        items = payload.get("organizations") or payload.get("companies") or payload.get("accounts") or payload.get("results") or []
        results: list[DiscoveryCompanyCandidate] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            organization_id = str(
                item.get("organization_id")
                or item.get("id")
                or item.get("apollo_id")
                or item.get("company_id")
                or ""
            ).strip()
            if not organization_id:
                continue
            location = item.get("organization_location") or item.get("location") or {}
            if isinstance(location, dict):
                country = location.get("country") or location.get("country_name")
                region = location.get("state") or location.get("region")
            else:
                country = item.get("country")
                region = item.get("region")
            results.append(
                DiscoveryCompanyCandidate(
                    source_provider=self.provider_name(),
                    source_record_id=organization_id,
                    name=str(item.get("name") or item.get("organization_name") or item.get("company_name") or "").strip(),
                    domain=(item.get("primary_domain") or item.get("domain") or item.get("website_url") or "").replace("https://", "").replace("http://", "").replace("www.", "").strip() or None,
                    industry=item.get("industry"),
                    company_size=str(item.get("company_size") or item.get("size") or item.get("organization_size") or "").strip() or None,
                    employee_count=self._to_int(item.get("estimated_num_employees") or item.get("organization_num_employees") or item.get("employees")),
                    country=str(country).strip() if country else None,
                    region=str(region).strip() if region else None,
                    description=item.get("short_description") or item.get("description") or item.get("headline"),
                    last_updated=self._parse_dt(item.get("updated_at") or item.get("last_updated_at") or item.get("last_updated")),
                    confidence=item.get("confidence") or item.get("score_label"),
                    source_metadata=item,
                )
            )
        return results

    def search_people(
        self,
        icp: ICPProductLine,
        organization: DiscoveryCompanyCandidate,
        *,
        page: int,
        per_page: int,
    ) -> list[DiscoveryContactCandidate]:
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "person_titles[]": icp.target_titles,
            "person_seniorities[]": icp.apollo_filters.get("person_seniorities", []),
            "q_organization_domains_list[]": [organization.domain] if organization.domain else [],
            "organization_ids[]": [organization.provider_organization_id],
            "organization_num_employees_ranges[]": self._employee_ranges(icp),
            "organization_locations[]": icp.country,
        }
        if icp.company_keywords:
            params["q_keywords"] = " ".join(icp.company_keywords[:5])
        payload = self._request("POST", "/mixed_people/api_search", params={k: v for k, v in params.items() if v})
        items = payload.get("people") or payload.get("contacts") or payload.get("results") or []
        results: list[DiscoveryContactCandidate] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            person_id = str(item.get("id") or item.get("person_id") or item.get("apollo_id") or "").strip()
            if not person_id:
                continue
            results.append(
                DiscoveryContactCandidate(
                    source_provider=self.provider_name(),
                    source_record_id=person_id,
                    organization_source_record_id=str(item.get("organization_id") or organization.source_record_id),
                    name=str(item.get("name") or f"{item.get('first_name', '')} {item.get('last_name', '')}").strip(),
                    title=str(item.get("title") or item.get("job_title") or "").strip(),
                    email=(item.get("email") or item.get("work_email") or item.get("contact_email") or None),
                    phone=(item.get("phone") or item.get("mobile_phone") or None),
                    linkedin_url=item.get("linkedin_url") or item.get("linkedin_url_normalized") or None,
                    seniority=str(item.get("seniority") or item.get("person_seniority") or "").strip() or None,
                    email_status=str(item.get("email_status") or item.get("contact_email_status") or "").strip() or None,
                    country=str(item.get("country") or "").strip() or None,
                    region=str(item.get("region") or "").strip() or None,
                    confidence=item.get("confidence") or item.get("score_label"),
                    source_metadata=item,
                )
            )
        return results

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            if value is None or value == "":
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                return None
        return None
