from __future__ import annotations

from collections.abc import Callable

from app.core.config import get_settings
from app.discovery.apollo_provider import ApolloProvider
from app.discovery.provider import DiscoveryProvider
from app.discovery.types import DiscoveryCompanyCandidate, DiscoveryContactCandidate, ICPProductLine
from app.discovery.search_strategy import SearchStrategy


class DiscoveryProviderManager:
    def __init__(
        self,
        *,
        providers: dict[str, DiscoveryProvider] | None = None,
        enabled_provider_names: list[str] | None = None,
        settings=None,
        provider_factory: Callable[[str], DiscoveryProvider] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._provider_factory = provider_factory or self._default_provider_factory
        self._providers = providers or {}
        self._enabled_provider_names = [
            name.strip().lower()
            for name in (enabled_provider_names or self._enabled_names_from_settings())
            if name.strip()
        ]
        self.last_search_diagnostic: dict | None = None

    def _enabled_names_from_settings(self) -> list[str]:
        value = getattr(self.settings, "discovery_enabled_providers", "apollo")
        return [item.strip().lower() for item in str(value).split(",") if item.strip()]

    def _default_provider_factory(self, provider_name: str) -> DiscoveryProvider:
        if provider_name == "apollo":
            return ApolloProvider()
        raise ValueError(f"Unsupported discovery provider: {provider_name}")

    def _get_provider(self, provider_name: str) -> DiscoveryProvider | None:
        provider = self._providers.get(provider_name)
        if provider is None and provider_name in self._enabled_provider_names:
            provider = self._provider_factory(provider_name)
            self._providers[provider_name] = provider
        return provider

    def enabled_provider_names(self) -> list[str]:
        return list(self._enabled_provider_names)

    def enabled_providers(self) -> list[DiscoveryProvider]:
        providers: list[DiscoveryProvider] = []
        for name in self._enabled_provider_names:
            provider = self._get_provider(name)
            if provider is not None:
                providers.append(provider)
        return providers

    def provider_for_name(self, provider_name: str) -> DiscoveryProvider | None:
        return self._get_provider(provider_name.lower())

    def search_organizations(self, icp: ICPProductLine, *, page: int, per_page: int) -> list[DiscoveryCompanyCandidate]:
        results: list[DiscoveryCompanyCandidate] = []
        for provider in self.enabled_providers():
            results.extend(provider.search_organizations(icp, page=page, per_page=per_page))
        return results

    def search_organizations_for_strategy(
        self,
        icp: ICPProductLine,
        strategy: SearchStrategy,
        *,
        page: int,
        per_page: int,
    ) -> list[DiscoveryCompanyCandidate]:
        results: list[DiscoveryCompanyCandidate] = []
        for provider in self.enabled_providers():
            try:
                results.extend(provider.search_organizations(icp, page=page, per_page=per_page, strategy=strategy))
            except TypeError:
                # Keeps older/fake providers compatible with the manager contract.
                results.extend(provider.search_organizations(icp, page=page, per_page=per_page))
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
        provider = self.provider_for_name(organization.source_provider)
        if provider is None:
            return []
        results = provider.search_people(icp, organization, page=page, per_page=per_page, title_filters=title_filters)
        self.last_search_diagnostic = getattr(provider, "last_people_diagnostic", None)
        return results

    def enrich_person(
        self,
        contact: DiscoveryContactCandidate,
        *,
        reveal_phone_number: bool = True,
    ) -> DiscoveryContactCandidate | None:
        provider = self.provider_for_name(contact.source_provider)
        if provider is None:
            return None
        return provider.enrich_person(contact, reveal_phone_number=reveal_phone_number)

    def enrich_organization(self, organization: DiscoveryCompanyCandidate) -> DiscoveryCompanyCandidate | None:
        provider = self.provider_for_name(organization.source_provider)
        if provider is None:
            return None
        return provider.enrich_organization(organization)

    def close(self) -> None:
        for provider in self._providers.values():
            close = getattr(provider, "close", None)
            if callable(close):
                close()


def create_default_provider_manager() -> DiscoveryProviderManager:
    return DiscoveryProviderManager()
