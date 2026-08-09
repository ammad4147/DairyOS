from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class WithdrawalPeriod:
    treatment_id: str
    animal_id: UUID
    start_time: datetime
    end_time: datetime
    withdrawn: bool = False

    def is_withdrawn(self, at: datetime | None = None) -> bool:
        at = at or datetime.utcnow()
        return self.withdrawn or at >= self.end_time

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

    def resolve_withdrawal(self, treatment_id: str):
        period = self._periods.get(treatment_id)
        if period:
            period.withdrawn = True
