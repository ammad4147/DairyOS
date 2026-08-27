"""Authoritative deployment activation and destructive-reset control."""

from __future__ import annotations

from datetime import datetime, timezone
import os

from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService

DEPLOYMENT_ACTIVE_KEY = "deployment_activated"
DEPLOYMENT_ACTIVATED_AT_KEY = "deployment_activated_at"
DEPLOYMENT_ACTIVATED_BY_KEY = "deployment_activated_by"
DEPLOYMENT_LAST_ACTION_KEY = "deployment_last_action"


class DeploymentControlError(RuntimeError):
    """Raised when deployment control cannot safely be performed."""


class DeploymentControlService:
    """Own the persisted gate between configuration and live operations."""

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
            "reset_protected": self.settings.is_reset_protected(),
        }

    def _require_password(self, password: str | None) -> None:
        if not self.settings.verify_reset_password(password):
            raise DeploymentControlError(
                "Deployment/reset password is not configured or is incorrect. "
                "Configure Reset Protection before using Deployment Controls."
            )

    def activate(self, *, password: str | None, updated_by: str) -> dict[str, object]:
        self._require_password(password)
        now = datetime.now(timezone.utc).isoformat()
        self.repository.set(DEPLOYMENT_ACTIVE_KEY, "true", updated_by=updated_by)
        self.repository.set(DEPLOYMENT_ACTIVATED_AT_KEY, now, updated_by=updated_by)
        self.repository.set(DEPLOYMENT_ACTIVATED_BY_KEY, updated_by, updated_by=updated_by)
        self.repository.set(DEPLOYMENT_LAST_ACTION_KEY, f"DEPLOYED:{now}", updated_by=updated_by)
        return self.status()

    def deactivate(self, *, password: str | None, updated_by: str) -> dict[str, object]:
        self._require_password(password)
        now = datetime.now(timezone.utc).isoformat()
        self.repository.set(DEPLOYMENT_ACTIVE_KEY, "false", updated_by=updated_by)
        self.repository.set(DEPLOYMENT_LAST_ACTION_KEY, f"RESET:{now}", updated_by=updated_by)
        return self.status()
