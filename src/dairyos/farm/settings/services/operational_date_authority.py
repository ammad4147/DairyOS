"""Authoritative farm operational-date resolver."""

from __future__ import annotations

from datetime import date

from dairyos.farm.settings.services.farm_settings_service import (
    FarmSettingsService,
)


class OperationalDateAuthority:
    """Resolve the farm operational date without retaining DB connections."""

    def __init__(
        self,
        settings_service: FarmSettingsService | None = None,
        repository_factory=None,
    ):
        self._settings_service = settings_service
        self._repository_factory = repository_factory

    def current_date(self) -> date:
        if self._settings_service is not None:
            return self._settings_service.get_operational_date()

        if self._repository_factory is not None:
            return FarmSettingsService(
                self._repository_factory.app_settings()
            ).get_operational_date()

        from dairyos.data.repositories.repository_factory import (
            RepositoryFactory,
        )

        factory = RepositoryFactory.create()

        try:
            return FarmSettingsService(
                factory.app_settings()
            ).get_operational_date()
        finally:
            factory.close()

    def current_date_string(self) -> str:
        return self.current_date().isoformat()
