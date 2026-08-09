from dairyos.farm.command_center.models.operational_gap import (
    OperationalGap,
)


class MissingInputDetectionService:
    """
    Detects expected operational activities
    that have not occurred.

    This service creates awareness only.
    It owns no operational actions.
    """

    def detect(
        self,
        farm_state,
    ):

        gaps = []

        milk = getattr(
            farm_state,
            "milk_production_summary",
            {},
        )

        if milk.get(
            "milking_events_count",
            0,
        ) == 0:

            gaps.append(
                OperationalGap(
                    area="MILK",
                    expected_activity="Daily milking",
                    message="No milk production entry recorded today",
                    severity="HIGH",
                )
            )


        feeding = getattr(
            farm_state,
            "feeding_status",
            {},
        )

        if not feeding.get(
            "events_today",
            0,
        ):

            gaps.append(
                OperationalGap(
                    area="FEEDING",
                    expected_activity="Daily feeding activity",
                    message="No feeding activity recorded today",
                    severity="MEDIUM",
                )
            )


        workforce = getattr(
            farm_state,
            "workforce_status",
            {},
        )

        if not workforce.get(
            "events_today",
            0,
        ):

            gaps.append(
                OperationalGap(
                    area="WORKFORCE",
                    expected_activity="Daily workforce activity",
                    message="No workforce activity recorded today",
                    severity="MEDIUM",
                )
            )


        return gaps
