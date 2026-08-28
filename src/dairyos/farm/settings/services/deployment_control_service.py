"""Authoritative deployment activation and destructive-reset control."""

from __future__ import annotations

from datetime import datetime, timezone
import os

from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService

DEPLOYMENT_ACTIVE_KEY = "deployment_activated"
DEPLOYMENT_ACTIVATED_AT_KEY = "deployment_activated_at"
DEPLOYMENT_ACTIVATED_BY_KEY = "deployment_activated_by"
DEPLOYMENT_LAST_ACTION_KEY = "deployment_last_action"


class DeploymentControlService:
    """Own the persisted gate between configuration and live operations.

    Deployment and reset are deliberately confirmation-gated, not password-
    gated. Authentication for other protected application actions remains
    separate from this lifecycle control.
    """

    def __init__(self, settings_service: FarmSettingsService):
        self.settings = settings_service
        self.repository = settings_service.repository

    def is_deployed(self) -> bool:
        value = self.repository.get(DEPLOYMENT_ACTIVE_KEY)
        if value is None:
            environment = os.getenv("DAIRYOS_ENV", "development").strip().lower()
            return environment not in {"production", "staging", "preprod"}
        return str(value).strip().lower() == "true"

    def status(self) -> dict[str, object]:
        return {
            "deployed": self.is_deployed(),
            "activated_at": self.repository.get(DEPLOYMENT_ACTIVATED_AT_KEY),
            "activated_by": self.repository.get(DEPLOYMENT_ACTIVATED_BY_KEY),
            "last_action": self.repository.get(DEPLOYMENT_LAST_ACTION_KEY),
        }

    def activate(self, *, updated_by: str) -> dict[str, object]:
        now = datetime.now(timezone.utc).isoformat()
        self.repository.set(DEPLOYMENT_ACTIVE_KEY, "true", updated_by=updated_by)
        self.repository.set(DEPLOYMENT_ACTIVATED_AT_KEY, now, updated_by=updated_by)
        self.repository.set(DEPLOYMENT_ACTIVATED_BY_KEY, updated_by, updated_by=updated_by)
        self.repository.set(DEPLOYMENT_LAST_ACTION_KEY, f"DEPLOYED:{now}", updated_by=updated_by)
        return self.status()

    def deactivate(self, *, updated_by: str) -> dict[str, object]:
        now = datetime.now(timezone.utc).isoformat()
        self.repository.set(DEPLOYMENT_ACTIVE_KEY, "false", updated_by=updated_by)
        self.repository.set(DEPLOYMENT_LAST_ACTION_KEY, f"RESET:{now}", updated_by=updated_by)
        return self.status()
