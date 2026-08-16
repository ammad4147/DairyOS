from dairyos.farm.day.models.farm_day import (
    FarmDay,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


class FarmDayRuntime:
    """
    Operational heartbeat for one farm day.

    Coordinates:

    - farm day lifecycle
    - operational entries
    - activity timeline

    Does not own domain logic.
    Domain services remain responsible
    for milk, feed, health and breeding.
    """

    def __init__(
        self,
        farm_id="TRIDENT-DAIRIES",
        operations_runtime=None,
        timeline_service=None,
        operational_date_authority=None,
    ):
        self.farm_id = farm_id

        self.operations_runtime = (
            operations_runtime
        )

        self.timeline_service = (
            timeline_service
        )

        self.operational_date_authority = (
            operational_date_authority
            or OperationalDateAuthority()
        )

        self.current_day = None

    def start_day(
        self,
        operational_date=None,
    ):
        if operational_date is None:
            operational_date = (
                self.operational_date_authority
                .current_date_string()
            )

        self.current_day = FarmDay(
            farm_id=self.farm_id,
            operational_date=operational_date,
        )

        return self.current_day

    def record_activity(
        self,
        activity,
    ):
        if self.current_day is None:
            raise RuntimeError(
                "Farm day has not started"
            )

        self.current_day.add_activity(
            activity
        )

        if self.timeline_service:
            self.timeline_service.record(
                activity
            )

        return activity

    def get_status(
        self,
    ):
        if self.current_day is None:
            return {
                "status": "not_started"
            }

        return {
            "day_id": self.current_day.day_id,
            "farm_id": self.current_day.farm_id,
            "date": self.current_day.operational_date,
            "status": self.current_day.status,
            "activities": len(
                self.current_day.activities
            ),
        }

    def close_day(
        self,
    ):
        if self.current_day is None:
            raise RuntimeError(
                "Farm day has not started"
            )

        self.current_day.close()

        return self.current_day
