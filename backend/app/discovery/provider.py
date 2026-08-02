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
    ) -> list[DiscoveryContactCandidate]:
        raise NotImplementedError
