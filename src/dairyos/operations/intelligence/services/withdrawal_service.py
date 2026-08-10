from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

@dataclass
class WithdrawalPeriod:
    treatment_id: str
    animal_id: Any
    start_time: datetime
    end_time: datetime
    withdrawn: bool = False

    def is_withdrawn(self, at: datetime | None = None) -> bool:
        if self.withdrawn:
            return True
        check_time = at or datetime.now(timezone.utc)
        start = self.start_time
        end = self.end_time
        # Normalize timezones for safe comparison
        if check_time.tzinfo is not None:
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
        else:
            if start.tzinfo is not None:
                start = start.replace(tzinfo=None)
            if end.tzinfo is not None:
                end = end.replace(tzinfo=None)
        return start <= check_time < end

class WithdrawalService:
    def __init__(self):
        self._periods: dict[str, WithdrawalPeriod] = {}

    def add_period(self, period: WithdrawalPeriod):
        self._periods[period.treatment_id] = period

    def is_withdrawn(self, treatment_id: str, at: datetime | None = None) -> bool:
        period = self._periods.get(treatment_id)
        if not period:
            return False
        return period.is_withdrawn(at)

    def is_animal_withdrawn(self, animal_id: Any, at: datetime | None = None) -> bool:
        str_id = str(animal_id)
        for period in self._periods.values():
            if str(period.animal_id) == str_id and period.is_withdrawn(at):
                return True
        return False

    def resolve_withdrawal(self, treatment_id: str):
        period = self._periods.get(treatment_id)
        if period:
            period.withdrawn = True

