from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ICPProductLine:
    product_name: str
    enabled: bool
    country: list[str]
    regions: list[str]
    target_industries: list[str]
    exclude_industries: list[str]
    company_keywords: list[str]
    exclude_keywords: list[str]
    apollo_filters: dict[str, Any]
    employee_min: int
    employee_max: int
    company_size: list[str]
    preferred_company_types: list[str]
    target_titles: list[str]
    preferred_titles: list[str]
    decision_level: list[str]
    lead_score_rules: dict[str, Any]
    search_frequency: str
    qualification_rules: dict[str, Any] = field(default_factory=dict)
    discovery_confidence_rules: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    profile_name: str | None = None
    target_segment: str | None = None
    exact_industries: list[str] = field(default_factory=list)
    related_industries: list[str] = field(default_factory=list)
    broad_industries: list[str] = field(default_factory=list)
    product_keywords: list[str] = field(default_factory=list)
    product_keyword_priorities: dict[str, int] = field(default_factory=dict)
    application_keywords: list[str] = field(default_factory=list)
    manufacturing_keywords: list[str] = field(default_factory=list)
    process_keywords: list[str] = field(default_factory=list)
    negative_keywords: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    apollo_search: dict[str, Any] = field(default_factory=dict)
    business_division: str | None = None
    states: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)
    apollo_industries: list[str] = field(default_factory=list)
    decision_maker_tiers: dict[str, list[str]] = field(default_factory=dict)
    manufacturing_cluster_preference: str | None = None
    product_recommendations: list[str] = field(default_factory=list)
    email_template_mapping: dict[str, Any] = field(default_factory=dict)
    description: str | None = None
    products: list[str] = field(default_factory=list)
    portfolio_applications: list[str] = field(default_factory=list)

    @property
    def search_profile_name(self) -> str:
        return self.profile_name or self.product_name


@dataclass(slots=True)
class DiscoveryCompanyCandidate:
    source_provider: str
    source_record_id: str
    name: str
    domain: str | None = None
    industry: str | None = None
    company_size: str | None = None
    employee_count: int | None = None
    country: str | None = None
    region: str | None = None
    city: str | None = None
    description: str | None = None
    last_updated: datetime | None = None
    confidence: str | None = None
    source_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def provider_name(self) -> str:
        return self.source_provider

    @property
    def provider_organization_id(self) -> str:
        return self.source_record_id

    @property
    def raw_payload(self) -> dict[str, Any]:
        return self.source_metadata


@dataclass(slots=True)
class DiscoveryContactCandidate:
    source_provider: str
    source_record_id: str
    organization_source_record_id: str | None
    name: str
    title: str
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    seniority: str | None = None
    email_status: str | None = None
    country: str | None = None
    region: str | None = None
    confidence: str | None = None
    contact_priority: str | None = None
    contact_priority_rank: int | None = None
    recommended_primary_contact: bool = False
    contact_selection_reason: str | None = None
    fallback_contact_used: bool = False
    source_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def provider_name(self) -> str:
        return self.source_provider

    @property
    def provider_person_id(self) -> str:
        return self.source_record_id

    @property
    def organization_provider_id(self) -> str | None:
        return self.organization_source_record_id

    @property
    def raw_payload(self) -> dict[str, Any]:
        return self.source_metadata


@dataclass(slots=True)
class DiscoveryScoreResult:
    score: float
    status: str
    needs_manual_review: bool
    reasons: list[str] = field(default_factory=list)
    matched_industry: bool = False
    matched_industry_level: str | None = None
    matched_industry_name: str | None = None
    matched_keyword: bool = False
    matched_keywords: list[str] = field(default_factory=list)
    matched_keyword_groups: list[str] = field(default_factory=list)
    matched_company_size: bool = False
    matched_decision_maker: bool = False
    matched_decision_maker_title: str | None = None
    verified_contact_present: bool = False
    applied_bonuses: list["QualificationImpact"] = field(default_factory=list)
    applied_penalties: list["QualificationImpact"] = field(default_factory=list)
    qualification_threshold: float | None = None
    manual_review_threshold: float | None = None
    evaluation_timestamp: datetime | None = None
    rule_results: list["QualificationRuleResult"] = field(default_factory=list)
    overall_recommendation: str | None = None
    final_confidence: str | None = None
    matched_cluster: str | None = None
    total_contacts_returned: int = 0
    selected_contact_name: str | None = None
    selected_contact_title: str | None = None
    selected_contact_priority: str | None = None
    selected_contact_reason: str | None = None
    fallback_contact_used: bool = False


@dataclass(slots=True)
class QualificationRuleResult:
    rule_name: str
    passed: bool
    points_awarded: float
    max_points: float
    reason: str


@dataclass(slots=True)
class QualificationImpact:
    label: str
    category: str
    points: float
    reason: str
    matched_value: str | None = None


@dataclass(slots=True)
class QualificationSummaryResult:
    companies_evaluated: int
    qualified: int
    manual_review: int
    rejected: int
    imported: int
    average_score: float
    top_failure_reasons: list[dict[str, int | str]]


@dataclass(slots=True)
class DiscoveryContext:
    product_line: ICPProductLine
    run_id: int
    api_calls_used: int = 0
    quota_remaining: int | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


ProviderOrganization = DiscoveryCompanyCandidate
ProviderPerson = DiscoveryContactCandidate
