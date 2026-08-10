from dataclasses import dataclass
from typing import List, Dict


@dataclass
class YieldDropAlert:
    animal_id: str
    baseline_yield_litres: float
    current_yield_litres: float
    drop_pct: float
    severity: str
    message: str


class YieldDropAlertService:
    """
    Evaluates individual cow milk yields against a 7-day moving average baseline.
    Flags yield drops exceeding threshold (default 15%).
    """

    def __init__(self, drop_threshold_pct: float = 15.0):
        self.drop_threshold_pct = drop_threshold_pct

    def evaluate_cow_yield(
        self,
        animal_id: str,
        recent_7_day_yields: List[float],
        current_yield_litres: float,
    ) -> YieldDropAlert | None:
        if not recent_7_day_yields:
            return None
        baseline = sum(recent_7_day_yields) / len(recent_7_day_yields)
        if baseline <= 0:
            return None
        if current_yield_litres < baseline:
            drop_amount = baseline - current_yield_litres
            drop_pct = (drop_amount / baseline) * 100
            if drop_pct >= self.drop_threshold_pct:
                severity = "CRITICAL" if drop_pct >= 30.0 else "WARNING"
                message = (
                    f"Animal {animal_id} milk yield dropped by {drop_pct:.1f}% "
                    f"below 7-day baseline ({current_yield_litres}L vs {baseline:.1f}L baseline)."
                )
                return YieldDropAlert(
                    animal_id=animal_id,
                    baseline_yield_litres=round(baseline, 2),
                    current_yield_litres=current_yield_litres,
                    drop_pct=round(drop_pct, 1),
                    severity=severity,
                    message=message,
                )
        return None
