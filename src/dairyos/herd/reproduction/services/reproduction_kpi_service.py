from dataclasses import dataclass
from datetime import date, datetime, timezone


@dataclass
class ReproductionKpiSummary:
    animal_id: str
    calving_interval_days: float | None = None
    days_open: int | None = None
    services_per_conception: float = 0.0
    conception_rate_pct: float = 0.0
    status: str = "NORMAL"


class ReproductionKpiService:
    """
    Calculates reproduction & fertility KPIs for dairy cows.
    """

    def calculate_calving_interval(
        self,
        previous_calving_date: date | datetime,
        current_calving_date: date | datetime,
    ) -> int:
        if isinstance(previous_calving_date, datetime):
            previous_calving_date = previous_calving_date.date()
        if isinstance(current_calving_date, datetime):
            current_calving_date = current_calving_date.date()
        return (current_calving_date - previous_calving_date).days

    def calculate_days_open(
        self,
        last_calving_date: date | datetime,
        conception_date: date | datetime,
    ) -> int:
        if isinstance(last_calving_date, datetime):
            last_calving_date = last_calving_date.date()
        if isinstance(conception_date, datetime):
            conception_date = conception_date.date()
        return (conception_date - last_calving_date).days

    def calculate_conception_rate(
        self,
        confirmed_pregnancies: int,
        total_inseminations: int,
    ) -> float:
        if total_inseminations == 0:
            return 0.0
        return round((confirmed_pregnancies / total_inseminations) * 100, 2)

    def calculate_services_per_conception(
        self,
        total_inseminations: int,
        total_conceptions: int,
    ) -> float:
        if total_conceptions == 0:
            return 0.0
        return round(total_inseminations / total_conceptions, 2)
