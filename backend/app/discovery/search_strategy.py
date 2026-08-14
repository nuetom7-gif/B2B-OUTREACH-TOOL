from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Any

from app.discovery.search_builder import ApolloSearchRequest, build_icp_search_request
from app.discovery.types import ICPProductLine


@dataclass(slots=True)
class SearchStrategy:
    name: str
    industry: str | None
    related_industry: bool
    product_keyword: str | None
    application_keywords: list[str]
    manufacturing_keywords: list[str]
    process_keywords: list[str]
    negative_keywords: list[str]
    keyword_tier: int = 2
    industry_priority: str = "exact"

    def to_metadata(self) -> dict[str, Any]:
        return asdict(self)


def plan_search_strategies(icp: ICPProductLine) -> list[SearchStrategy]:
    """Create focused provider-neutral searches from one Industry Pack."""
    exact = list(dict.fromkeys(icp.exact_industries or icp.target_industries))
    related = [item for item in dict.fromkeys(icp.related_industries) if item not in exact]
    industries = [(item, False) for item in exact] + [(item, True) for item in related]
    products = list(dict.fromkeys(icp.product_keywords or icp.company_keywords))
    strategies: list[SearchStrategy] = []

    # Search every product signal against every configured industry. The
    # previous cyclic assignment silently skipped most valid combinations.
    for industry, related_industry in industries:
        for keyword in products:
            strategies.append(
                SearchStrategy(
                    name=f"{icp.search_profile_name} / {industry} / {keyword}",
                    industry=industry,
                    related_industry=related_industry,
                    product_keyword=keyword,
                    application_keywords=list(icp.application_keywords),
                    manufacturing_keywords=list(icp.manufacturing_keywords),
                    process_keywords=list(icp.process_keywords),
                    negative_keywords=list(icp.negative_keywords or icp.exclude_keywords),
                    keyword_tier=int(icp.product_keyword_priorities.get(keyword, 2)),
                    industry_priority="related" if related_industry else "exact",
                )
            )

    if not strategies:
        for industry, related_industry in industries:
            strategies.append(
                SearchStrategy(
                    name=f"{icp.search_profile_name} / {industry}",
                    industry=industry,
                    related_industry=related_industry,
                    product_keyword=None,
                    application_keywords=list(icp.application_keywords),
                    manufacturing_keywords=list(icp.manufacturing_keywords),
                    process_keywords=list(icp.process_keywords),
                    negative_keywords=list(icp.negative_keywords or icp.exclude_keywords),
                    keyword_tier=3,
                    industry_priority="related" if related_industry else "exact",
                )
            )

    return strategies or [
        SearchStrategy(
            name=icp.search_profile_name,
            industry=None,
            related_industry=False,
            product_keyword=None,
            application_keywords=list(icp.application_keywords),
            manufacturing_keywords=list(icp.manufacturing_keywords),
            process_keywords=list(icp.process_keywords),
            negative_keywords=list(icp.negative_keywords or icp.exclude_keywords),
            keyword_tier=3,
            industry_priority="exact",
        )
    ]


def build_provider_request(icp: ICPProductLine, strategy: SearchStrategy) -> ApolloSearchRequest:
    request = build_icp_search_request(icp)
    return ApolloSearchRequest(
        product_line=request.product_line,
        profile_name=request.profile_name,
        countries=request.countries,
        states=request.states,
        cities=request.cities,
        employee_ranges=request.employee_ranges,
        exact_industries=[strategy.industry] if strategy.industry and not strategy.related_industry else [],
        related_industries=[strategy.industry] if strategy.industry and strategy.related_industry else [],
        broad_industries=request.broad_industries,
        product_keywords=[strategy.product_keyword] if strategy.product_keyword else [],
        application_keywords=request.application_keywords,
        manufacturing_keywords=request.manufacturing_keywords,
        process_keywords=request.process_keywords,
        negative_keywords=request.negative_keywords,
        decision_makers=request.decision_makers,
        provider_filters=request.provider_filters,
    )


def optimize_search_strategies(
    icp: ICPProductLine,
    strategies: list[SearchStrategy],
) -> list[SearchStrategy]:
    """Remove redundant/broad queries and order the most specific first."""
    broad_terms = {_normalize_search_text(item) for item in icp.broad_industries if item.strip()}
    unique: dict[tuple[str, str], SearchStrategy] = {}
    for strategy in strategies:
        industry = _normalize_search_text(strategy.industry)
        keyword = _normalize_search_text(strategy.product_keyword)
        if keyword and keyword in broad_terms:
            continue
        key = (industry, keyword)
        unique.setdefault(key, strategy)

    def sort_key(strategy: SearchStrategy) -> tuple[int, int, int, str]:
        keyword = strategy.product_keyword or ""
        return (
            strategy.keyword_tier,
            0 if strategy.industry_priority == "exact" else 1,
            -len(keyword.split()),
            strategy.name.lower(),
        )

    return sorted(unique.values(), key=sort_key)


def _normalize_search_text(value: str | None) -> str:
    """Make punctuation, spacing, and case-only query variants equivalent."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (value or "").lower())).strip()
