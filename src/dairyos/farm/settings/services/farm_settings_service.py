"""Farm settings service.

Settings are persisted through the authoritative ``app_settings`` key/value
repository. They configure farm identity, operational-date interpretation,
and dashboard defaults. They never replace domain facts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_FARM_NAME = "Trident Dairies"
DEFAULT_ANIMAL_ID_PREFIX = "TD"
DEFAULT_TIMEZONE = "Asia/Karachi"
DEFAULT_OPERATIONAL_DATE_CONVENTION = "FARM_LOCAL_DATE"
DEFAULT_DASHBOARD_TREND_PERIOD = "7d"
DEFAULT_DASHBOARD_CARD_VISIBILITY = {
    "milk": True,
    "herd": True,
    "health": True,
    "finance": True,
    "analytics": True,
}
DEFAULT_ALERT_PREFERENCES = {}


def _json_loads(
    value,
    default,
):
    if not value:
        return default

    try:
        loaded = json.loads(value)

        return (
            loaded
            if isinstance(loaded, type(default))
            else default
        )
    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return default


class FarmSettingsService:
    def __init__(self, repository):
        self.repository = repository

    # ------------------------------------------------------------------
    # Farm identity
    # ------------------------------------------------------------------

    def get_farm_name(self) -> str:
        value = self.repository.get(
            "farm_name",
            DEFAULT_FARM_NAME,
        )

        value = str(value or "").strip()

        return value or DEFAULT_FARM_NAME

    def get_animal_id_prefix(self) -> str:
        prefix = self.repository.get(
            "animal_id_prefix",
            DEFAULT_ANIMAL_ID_PREFIX,
        )

        prefix = str(
            prefix or ""
        ).strip().upper()

        return prefix or DEFAULT_ANIMAL_ID_PREFIX

    # ------------------------------------------------------------------
    # Operational date authority
    # ------------------------------------------------------------------

    def get_timezone(self) -> str:
        timezone_name = str(
            self.repository.get(
                "timezone",
                DEFAULT_TIMEZONE,
            )
            or DEFAULT_TIMEZONE
        ).strip()

        try:
            ZoneInfo(timezone_name)
        except (
            ZoneInfoNotFoundError,
            ValueError,
        ):
            return DEFAULT_TIMEZONE

        return timezone_name

    def get_timezone_info(self):
        return ZoneInfo(
            self.get_timezone()
        )

    def get_operational_date_convention(self) -> str:
        convention = str(
            self.repository.get(
                "operational_date_convention",
                DEFAULT_OPERATIONAL_DATE_CONVENTION,
            )
            or DEFAULT_OPERATIONAL_DATE_CONVENTION
        ).strip().upper()

        if convention != DEFAULT_OPERATIONAL_DATE_CONVENTION:
            return DEFAULT_OPERATIONAL_DATE_CONVENTION

        return convention

    def get_operational_date(self):
        """Return the current farm operational date.

        The system's configured farm timezone determines the calendar date.
        This is deliberately date-only; no UI-relative 'today/yesterday'
        marker is persisted or returned.
        """
        return datetime.now(
            timezone.utc
        ).astimezone(
            self.get_timezone_info()
        ).date()

    # ------------------------------------------------------------------
    # Dashboard / UI preferences
    # ------------------------------------------------------------------

    def get_dashboard_preferences(self) -> dict:
        trend_period = str(
            self.repository.get(
                "dashboard_default_trend_period",
                DEFAULT_DASHBOARD_TREND_PERIOD,
            )
            or DEFAULT_DASHBOARD_TREND_PERIOD
        ).strip()

        if trend_period not in {
            "7d",
            "30d",
            "3mo",
            "6mo",
            "1y",
        }:
            trend_period = DEFAULT_DASHBOARD_TREND_PERIOD

        visibility = _json_loads(
            self.repository.get(
                "dashboard_card_visibility"
            ),
            {},
        )

        merged_visibility = dict(
            DEFAULT_DASHBOARD_CARD_VISIBILITY
        )
        merged_visibility.update(
            {
                key: bool(value)
                for key, value in visibility.items()
                if key in DEFAULT_DASHBOARD_CARD_VISIBILITY
            }
        )

        return {
            "default_trend_period": trend_period,
            "card_visibility": merged_visibility,
        }

    def get_alert_preferences(self) -> dict:
        return _json_loads(
            self.repository.get(
                "alert_preferences"
            ),
            dict(DEFAULT_ALERT_PREFERENCES),
        )

    # ------------------------------------------------------------------
    # Public settings read model
    # ------------------------------------------------------------------

    def get_public_settings(self) -> dict:
        return {
            "farm_name": self.get_farm_name(),
            "animal_id_prefix": self.get_animal_id_prefix(),
            "timezone": self.get_timezone(),
            "operational_date_convention": (
                self.get_operational_date_convention()
            ),
            "current_operational_date": (
                self.get_operational_date().isoformat()
            ),
            "dashboard": self.get_dashboard_preferences(),
            "alerts": self.get_alert_preferences(),
        }

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def update_identity(
        self,
        *,
        farm_name: str | None = None,
        animal_id_prefix: str | None = None,
        updated_by: str | None = None,
    ) -> dict:
        if farm_name is not None:
            farm_name = farm_name.strip()

            if not farm_name:
                raise ValueError(
                    "farm_name cannot be blank"
                )

            self.repository.set(
                "farm_name",
                farm_name,
                updated_by=updated_by,
            )

        if animal_id_prefix is not None:
            prefix = (
                animal_id_prefix
                .strip()
                .upper()
            )

            if not (
                1 <= len(prefix) <= 6
            ) or not prefix.isalpha():
                raise ValueError(
                    "animal_id_prefix must be 1-6 letters (e.g. \"TD\")"
                )

            self.repository.set(
                "animal_id_prefix",
                prefix,
                updated_by=updated_by,
            )

        return self.get_public_settings()

    def update_operational_settings(
        self,
        *,
        timezone_name: str | None = None,
        operational_date_convention: str | None = None,
        updated_by: str | None = None,
    ) -> dict:
        if timezone_name is not None:
            timezone_name = timezone_name.strip()

            try:
                ZoneInfo(timezone_name)
            except (
                ZoneInfoNotFoundError,
                ValueError,
            ) as exc:
                raise ValueError(
                    f"Unknown IANA timezone: {timezone_name}"
                ) from exc

            self.repository.set(
                "timezone",
                timezone_name,
                updated_by=updated_by,
            )

        if operational_date_convention is not None:
            convention = (
                operational_date_convention
                .strip()
                .upper()
            )

            if (
                convention
                != DEFAULT_OPERATIONAL_DATE_CONVENTION
            ):
                raise ValueError(
                    "operational_date_convention must be "
                    "FARM_LOCAL_DATE"
                )

            self.repository.set(
                "operational_date_convention",
                convention,
                updated_by=updated_by,
            )

        return self.get_public_settings()

    def update_dashboard_preferences(
        self,
        *,
        default_trend_period: str | None = None,
        card_visibility: dict | None = None,
        updated_by: str | None = None,
    ) -> dict:
        if default_trend_period is not None:
            trend_period = (
                default_trend_period
                .strip()
            )

            if trend_period not in {
                "7d",
                "30d",
                "3mo",
                "6mo",
                "1y",
            }:
                raise ValueError(
                    "default_trend_period must be one of "
                    "7d, 30d, 3mo, 6mo, 1y"
                )

            self.repository.set(
                "dashboard_default_trend_period",
                trend_period,
                updated_by=updated_by,
            )

        if card_visibility is not None:
            if not isinstance(
                card_visibility,
                dict,
            ):
                raise ValueError(
                    "card_visibility must be an object"
                )

            normalized = {
                key: bool(value)
                for key, value in card_visibility.items()
                if key in DEFAULT_DASHBOARD_CARD_VISIBILITY
            }

            self.repository.set(
                "dashboard_card_visibility",
                json.dumps(
                    normalized,
                    sort_keys=True,
                ),
                updated_by=updated_by,
            )

        return self.get_public_settings()

    def update_alert_preferences(
        self,
        *,
        preferences: dict,
        updated_by: str | None = None,
    ) -> dict:
        if not isinstance(
            preferences,
            dict,
        ):
            raise ValueError(
                "alert preferences must be an object"
            )

        self.repository.set(
            "alert_preferences",
            json.dumps(
                preferences,
                sort_keys=True,
            ),
            updated_by=updated_by,
        )

        return self.get_public_settings()
