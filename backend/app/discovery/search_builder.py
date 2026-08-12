from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.discovery.types import ICPProductLine


@dataclass(slots=True)
class ApolloSearchRequest:
    """Provider-neutral search intent before Apollo parameter translation."""

    product_line: str
    profile_name: str
    countries: list[str]
    states: list[str]
    employee_ranges: list[str]
    exact_industries: list[str]
    related_industries: list[str]
    broad_industries: list[str]
    product_keywords: list[str]
    application_keywords: list[str]
    manufacturing_keywords: list[str]
    process_keywords: list[str]
    negative_keywords: list[str]
    decision_makers: list[str]
    provider_filters: dict[str, Any]

    @property
    def organization_terms(self) -> list[str]:
        return list(dict.fromkeys(self.exact_industries + self.related_industries + self.broad_industries))

    @property
    def all_keywords(self) -> list[str]:
        return list(dict.fromkeys(self.product_keywords + self.manufacturing_keywords + self.process_keywords))

    @property
    def apollo_keywords(self) -> list[str]:
        return list(dict.fromkeys(self.product_keywords))


def build_icp_search_request(
    icp: ICPProductLine,
    *,
    country: str | None = None,
    state: str | None = None,
    employee_min: int | None = None,
    employee_max: int | None = None,
) -> ApolloSearchRequest:
    countries = [country.strip()] if country and country.strip() else (icp.locations or icp.country)
    minimum = icp.employee_min if employee_min is None else employee_min
    maximum = icp.employee_max if employee_max is None else employee_max
    ranges = [f"{max(1, minimum)},{max(minimum, maximum)}"] if minimum or maximum else []
    return ApolloSearchRequest(
        product_line=icp.product_name,
        profile_name=icp.search_profile_name,
        countries=countries,
        states=[state.strip()] if state and state.strip() else icp.states,
        employee_ranges=ranges,
        exact_industries=icp.exact_industries or icp.target_industries,
        related_industries=icp.related_industries or icp.preferred_company_types,
        broad_industries=icp.broad_industries or icp.company_keywords,
        product_keywords=icp.product_keywords or icp.company_keywords,
        application_keywords=icp.application_keywords,
        manufacturing_keywords=icp.manufacturing_keywords,
        process_keywords=icp.process_keywords,
        negative_keywords=icp.negative_keywords or icp.exclude_keywords,
        decision_makers=icp.target_titles,
        provider_filters={**icp.apollo_filters, **icp.apollo_search},
    )
