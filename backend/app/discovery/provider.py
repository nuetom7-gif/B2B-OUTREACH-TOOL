from __future__ import annotations

from abc import ABC, abstractmethod

from app.discovery.types import DiscoveryCompanyCandidate, DiscoveryContactCandidate, ICPProductLine


class DiscoveryProvider(ABC):
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def search_organizations(self, icp: ICPProductLine, *, page: int, per_page: int) -> list[DiscoveryCompanyCandidate]:
        raise NotImplementedError

    @abstractmethod
    def search_people(
        self,
        icp: ICPProductLine,
        organization: DiscoveryCompanyCandidate,
        *,
        page: int,
        per_page: int,
        title_filters: list[str] | None = None,
    ) -> list[DiscoveryContactCandidate]:
        raise NotImplementedError

    def enrich_person(
        self,
        contact: DiscoveryContactCandidate,
    ) -> DiscoveryContactCandidate | None:
        """Return enriched data for one selected contact, when supported."""
        return None

    def enrich_organization(
        self,
        organization: DiscoveryCompanyCandidate,
    ) -> DiscoveryCompanyCandidate | None:
        """Return enriched data for one identified organization, when supported."""
        return None
