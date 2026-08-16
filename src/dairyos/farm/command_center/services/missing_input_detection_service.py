from dairyos.farm.command_center.models.operational_gap import (
    OperationalGap,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


class MissingInputDetectionService:
    """Detect required daily activities from canonical current farm state."""

    def __init__(
        self,
        operational_date_authority=None,
    ):
        self.operational_date_authority = (
            operational_date_authority
            or OperationalDateAuthority()
        )

    def detect(
        self,
        farm_state,
    ):
        gaps = []

        operational_date = str(
            getattr(
                farm_state,
                "operational_date",
                "",
            )
            or ""
        )

        current_operational_date = (
            self.operational_date_authority
            .current_date_string()
        )

        is_current_day = (
            operational_date
            == current_operational_date
        )

        milk = getattr(
            farm_state,
            "milk_production_summary",
            {},
        ) or {}

        milk_events = int(
            milk.get(
                "milking_events_count",
                0,
            )
            or 0
        )

        if not is_current_day or milk_events == 0:
            gaps.append(
                OperationalGap(
                    area="MILK",
                    expected_activity="Daily milking",
                    message=(
                        "No milk production entry recorded "
                        "for the current operational date"
                    ),
                    severity="HIGH",
                )
            )

        feeding = getattr(
            farm_state,
            "feeding_status",
            {},
        ) or {}

        if (
            not is_current_day
            or not self._has_current_activity(
                feeding
            )
        ):
            gaps.append(
                OperationalGap(
                    area="FEEDING",
                    expected_activity=(
                        "Daily feeding activity"
                    ),
                    message=(
                        "No feeding activity recorded "
                        "for the current operational date"
                    ),
                    severity="MEDIUM",
                )
            )

        workforce = getattr(
            farm_state,
            "workforce_status",
            {},
        ) or {}

        if (
            not is_current_day
            or not self._has_current_activity(
                workforce
            )
        ):
            gaps.append(
                OperationalGap(
                    area="WORKFORCE",
                    expected_activity=(
                        "Daily workforce activity"
                    ),
                    message=(
                        "No workforce activity recorded "
                        "for the current operational date"
                    ),
                    severity="MEDIUM",
                )
            )

        return gaps

    @staticmethod
    def _has_current_activity(
        status,
    ):
        if not status:
            return False

        for value in status.values():
            if value is None:
                continue

            if isinstance(value, dict):
                if value.get(
                    "status"
                ) not in (
                    None,
                    "UNKNOWN",
                ):
                    return True

                if any(
                    item not in (
                        None,
                        "",
                        0,
                        False,
                        [],
                    )
                    for item in value.values()
                    if item != "UNKNOWN"
                ):
                    return True

            elif value not in (
                "UNKNOWN",
                "",
                None,
                0,
                False,
            ):
                return True

        return False
