from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.discovery.provider import DiscoveryProvider
from app.discovery.search_builder import build_icp_search_request
from app.discovery.search_strategy import SearchStrategy, build_provider_request
from app.discovery.diagnostics import extract_organization_fields, people_field_mapping, unused_organization_fields
from app.discovery.types import DiscoveryCompanyCandidate, DiscoveryContactCandidate, ICPProductLine


class ApolloProviderError(RuntimeError):
    pass


class ApolloRateLimitError(ApolloProviderError):
    pass


class ApolloProvider(DiscoveryProvider):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_calls_used = 0
        self._client = httpx.Client(
            base_url=self.settings.apollo_base_url.rstrip("/"),
            timeout=30.0,
            headers={
                "x-api-key": self.settings.apollo_api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        self._last_call_monotonic = 0.0
        self.last_people_diagnostic: dict | None = None
        self.last_enrichment_diagnostic: dict | None = None

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
                self.api_calls_used += 1
                payload = response.json()
                if isinstance(payload, dict):
                    return payload
                return {"results": payload}
            except httpx.HTTPError as exc:
                if attempt + 1 >= self.settings.apollo_retry_limit:
                    raise ApolloProviderError(f"Apollo request failed: {exc}") from exc
                time.sleep(2**attempt)
        raise ApolloProviderError("Apollo request failed unexpectedly")

    def _common_org_params(self, icp: ICPProductLine, *, page: int, per_page: int, strategy: SearchStrategy | None = None) -> dict[str, Any]:
        search = build_provider_request(icp, strategy) if strategy else build_icp_search_request(icp)
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }
        if search.countries or search.states:
            params["organization_locations[]"] = search.countries + search.states
        if search.employee_ranges:
            params["organization_num_employees_ranges[]"] = search.employee_ranges
        # Apollo's documented company-keyword filter is the API equivalent of
        # the AI panel's "Company Keywords Contain ANY Of" chips. Industry
        # labels are kept in the ICP for qualification and diagnostics; they
        # must not be sent here as keyword tags.
        keyword_tags = list(
            dict.fromkeys(
                search.product_keywords
                + search.manufacturing_keywords
                + search.application_keywords
            )
        )
        if keyword_tags:
            params["q_organization_keyword_tags[]"] = keyword_tags
        if search.negative_keywords:
            params["excluded_organization_keyword_tags[]"] = search.negative_keywords
        params.update({key: value for key, value in search.provider_filters.items() if key.startswith("organization_")})
        return params

    def search_organizations(self, icp: ICPProductLine, *, page: int, per_page: int, strategy: SearchStrategy | None = None) -> list[DiscoveryCompanyCandidate]:
        request_params = self._common_org_params(icp, page=page, per_page=per_page, strategy=strategy)
        payload = self._request(
            "POST",
            "/mixed_companies/search",
            params=request_params,
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
            extracted, mapping = extract_organization_fields(item)
            location = item.get("organization_location") or item.get("location") or {}
            if isinstance(location, dict):
                country = location.get("country") or location.get("country_name") or extracted["Country"]
                region = location.get("state") or location.get("region") or extracted["Region"]
                city = location.get("city") or location.get("locality") or location.get("metro_area") or location.get("town") or extracted["City"]
            else:
                country, region, city = extracted["Country"], extracted["Region"], extracted["City"]
            domain = str(extracted["Website"] or "").replace("https://", "").replace("http://", "").replace("www.", "").strip() or None
            industry = str(extracted["Industry"] or "").strip() or None
            candidate = DiscoveryCompanyCandidate(
                    source_provider=self.provider_name(),
                    source_record_id=organization_id,
                    name=str(extracted["Company Name"] or "").strip(),
                    domain=domain,
                    industry=industry,
                    company_size=str(item.get("company_size") or item.get("size") or item.get("organization_size") or "").strip() or None,
                    employee_count=self._to_int(extracted["Employee Count"]),
                    country=str(country).strip() if country else None,
                    region=str(region).strip() if region else None,
                    city=str(city).strip() if city else None,
                    description=str(extracted["Description"] or "").strip() or None,
                    last_updated=self._parse_dt(item.get("updated_at") or item.get("last_updated_at") or item.get("last_updated")),
                    confidence=item.get("confidence") or item.get("score_label"),
                    source_metadata=item,
                )
            normalized = {
                "name": candidate.name,
                "domain": candidate.domain,
                "industry": candidate.industry,
                "employee_count": candidate.employee_count,
                "country": candidate.country,
                "region": candidate.region,
                "city": candidate.city,
                "description": candidate.description,
                "linkedin_url": extracted["LinkedIn"],
                "revenue": extracted["Revenue"],
                "technologies": extracted["Technologies"],
            }
            if self.settings.discovery_diagnostic_mode:
                candidate.source_metadata = {
                    "apollo_raw_record": item,
                    "apollo_raw_response": payload,
                "apollo_request": {"method": "POST", "path": "/mixed_companies/search", "params": request_params},
                    "search_strategy": strategy.to_metadata() if strategy else None,
                    "field_mapping": mapping,
                    "unused_apollo_fields": unused_organization_fields(item, mapping),
                    "normalized_company": normalized,
                }
            results.append(candidate)
        return results

    def search_people(
        self,
        icp: ICPProductLine,
        organization: DiscoveryCompanyCandidate,
        *,
        page: int,
        per_page: int,
        title_filters: list[str] | None = None,
    ) -> list[DiscoveryContactCandidate]:
        search = build_icp_search_request(icp)
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "person_seniorities[]": icp.apollo_filters.get("person_seniorities", []),
            "q_organization_domains_list[]": [organization.domain] if organization.domain else [],
            "organization_ids[]": [organization.provider_organization_id],
            "organization_num_employees_ranges[]": search.employee_ranges,
            "organization_locations[]": search.countries + search.states,
        }
        effective_titles = title_filters if title_filters is not None else icp.target_titles
        if effective_titles:
            params["person_titles[]"] = effective_titles
        request_params = {k: v for k, v in params.items() if v}
        payload = self._request("POST", "/mixed_people/api_search", params=request_params)
        self.last_people_diagnostic = (
            {
                "request": {"method": "POST", "path": "/mixed_people/api_search", "params": request_params},
                "response": payload,
                "contacts_returned": 0,
            }
            if self.settings.discovery_diagnostic_mode
            else None
        )
        items = payload.get("people") or payload.get("contacts") or payload.get("results") or []
        results: list[DiscoveryContactCandidate] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            person_id = str(item.get("id") or item.get("person_id") or item.get("apollo_id") or "").strip()
            if not person_id:
                continue
            candidate = DiscoveryContactCandidate(
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
            normalized = {
                "name": candidate.name,
                "title": candidate.title,
                "email": candidate.email,
                "phone": candidate.phone,
                "linkedin_url": candidate.linkedin_url,
                "email_status": candidate.email_status,
                "country": candidate.country,
                "region": candidate.region,
            }
            if self.settings.discovery_diagnostic_mode:
                candidate.source_metadata = {
                    "apollo_raw_record": item,
                    "apollo_raw_response": payload,
                    "apollo_request": {"method": "POST", "path": "/mixed_people/api_search", "params": request_params},
                    "field_mapping": people_field_mapping(item, normalized),
                    "normalized_contact": normalized,
                }
            results.append(candidate)
        if self.last_people_diagnostic is not None:
            self.last_people_diagnostic["contacts_returned"] = len(results)
        return results

    def enrich_person(self, contact: DiscoveryContactCandidate) -> DiscoveryContactCandidate | None:
        request_params = {
            "person_id": contact.provider_person_id,
            "reveal_personal_emails": False,
            "reveal_phone_number": False,
        }
        payload = self._request("POST", "/people/match", params=request_params)
        self.last_enrichment_diagnostic = {
            "request": {"method": "POST", "path": "/people/match", "params": request_params},
            "response": payload,
            "person_id": contact.provider_person_id,
        }
        item = payload.get("person") or payload.get("contact") or payload.get("result")
        if not isinstance(item, dict):
            contact.source_metadata["apollo_enrichment"] = self.last_enrichment_diagnostic
            return None
        name = str(item.get("name") or contact.name).strip()
        title = str(item.get("title") or item.get("job_title") or contact.title).strip()
        email = item.get("email") or item.get("work_email") or contact.email
        phone = item.get("phone") or item.get("direct_phone") or item.get("mobile_phone") or contact.phone
        email_status = str(
            item.get("email_status") or item.get("contact_email_status") or contact.email_status or ""
        ).strip() or None
        return DiscoveryContactCandidate(
            source_provider=contact.source_provider,
            source_record_id=contact.source_record_id,
            organization_source_record_id=contact.organization_source_record_id,
            name=name,
            title=title,
            email=email,
            phone=phone,
            linkedin_url=item.get("linkedin_url") or contact.linkedin_url,
            seniority=str(item.get("seniority") or contact.seniority or "").strip() or None,
            email_status=email_status,
            country=str(item.get("country") or contact.country or "").strip() or None,
            region=str(item.get("region") or contact.region or "").strip() or None,
            confidence=item.get("confidence") or contact.confidence,
            contact_priority=contact.contact_priority,
            contact_priority_rank=contact.contact_priority_rank,
            recommended_primary_contact=contact.recommended_primary_contact,
            contact_selection_reason=contact.contact_selection_reason,
            fallback_contact_used=contact.fallback_contact_used,
            source_metadata={
                **contact.source_metadata,
                "apollo_enrichment": self.last_enrichment_diagnostic,
                "normalized_contact": {
                    "name": name,
                    "title": title,
                    "email": email,
                    "phone": phone,
                    "linkedin_url": item.get("linkedin_url") or contact.linkedin_url,
                    "email_status": email_status,
                },
            },
        )

    def enrich_organization(self, organization: DiscoveryCompanyCandidate) -> DiscoveryCompanyCandidate | None:
        raw = organization.source_metadata.get("apollo_raw_record", organization.source_metadata)
        if not isinstance(raw, dict):
            raw = {}
        request_params: dict[str, Any] = {"name": organization.name}
        if organization.domain:
            request_params["domain"] = organization.domain
        linkedin_url = raw.get("linkedin_url") or raw.get("linkedin_url_normalized")
        if linkedin_url:
            request_params["linkedin_url"] = linkedin_url
        # Apollo documents this endpoint as GET, despite older internal notes
        # referring to it as POST /organizations/enrich.
        payload = self._request("GET", "/organizations/enrich", params=request_params)
        self.last_enrichment_diagnostic = {
            "request": {"method": "GET", "path": "/organizations/enrich", "params": request_params},
            "response": payload,
            "organization_id": organization.provider_organization_id,
        }
        item = payload.get("organization") or payload.get("company") or payload.get("account")
        if not isinstance(item, dict):
            organization.source_metadata["apollo_organization_enrichment"] = self.last_enrichment_diagnostic
            return None
        extracted, mapping = extract_organization_fields(item)
        location = item.get("organization_location") or item.get("location") or {}
        if not isinstance(location, dict):
            location = {}
        enriched_raw = {**raw, **item}
        metadata = {
            **organization.source_metadata,
            "apollo_raw_record": enriched_raw,
            "apollo_organization_enrichment": self.last_enrichment_diagnostic,
            "organization_enrichment_field_mapping": mapping,
            "normalized_company": {
                "name": extracted["Company Name"] or organization.name,
                "domain": extracted["Website"] or organization.domain,
                "industry": extracted["Industry"],
                "employee_count": extracted["Employee Count"],
                "country": extracted["Country"],
                "region": extracted["Region"],
                "city": extracted["City"],
                "description": extracted["Description"],
                "linkedin_url": extracted["LinkedIn"] or linkedin_url,
            },
        }
        domain = str(extracted["Website"] or organization.domain or "").replace("https://", "").replace("http://", "").replace("www.", "").strip() or None
        return DiscoveryCompanyCandidate(
            source_provider=organization.source_provider,
            source_record_id=organization.source_record_id,
            name=str(extracted["Company Name"] or organization.name).strip(),
            domain=domain,
            industry=str(extracted["Industry"] or organization.industry or "").strip() or None,
            company_size=organization.company_size,
            employee_count=self._to_int(extracted["Employee Count"]) or organization.employee_count,
            country=str(location.get("country") or extracted["Country"] or organization.country or "").strip() or None,
            region=str(location.get("state") or location.get("region") or extracted["Region"] or organization.region or "").strip() or None,
            city=str(location.get("city") or extracted["City"] or organization.city or "").strip() or None,
            description=str(extracted["Description"] or organization.description or "").strip() or None,
            last_updated=organization.last_updated,
            confidence=organization.confidence,
            source_metadata=metadata,
        )

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
