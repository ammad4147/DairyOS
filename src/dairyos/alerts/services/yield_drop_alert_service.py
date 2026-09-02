from dataclasses import dataclass
from typing import Dict, List


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
    Evaluate an individual animal against its prior three recorded daily yields.

    DairyOS milk-yield policy:
    - drop < 15%: normal; no watchlist alert
    - drop >= 15% and < 20%: warning / Yellow
    - drop >= 20%: critical / Red

    ``recent_7_day_yields`` is retained as the parameter name for compatibility
    with older callers, but only the latest three prior observations form the
    governed baseline.
    """

    def __init__(self, drop_threshold_pct: float = 15.0):
        self.drop_threshold_pct = max(15.0, float(drop_threshold_pct))

    def evaluate_cow_yield(
        self,
        animal_id: str,
        recent_7_day_yields: List[float],
        current_yield_litres: float,
    ) -> YieldDropAlert | None:
        prior_three = [
            float(value)
            for value in recent_7_day_yields[-3:]
            if value is not None
        ]

        if len(prior_three) < 3:
            return None

        baseline = sum(prior_three) / 3.0
        if baseline <= 0:
            return None

        current = float(current_yield_litres)
        if current >= baseline:
            return None

        drop_amount = baseline - current
        drop_pct = (drop_amount / baseline) * 100.0

        if drop_pct < self.drop_threshold_pct:
            return None

        severity = "CRITICAL" if drop_pct >= 20.0 else "WARNING"
        message = (
            f"Animal {animal_id} milk yield dropped by {drop_pct:.1f}% "
            f"below prior 3-day average ({current:.1f}L vs "
            f"{baseline:.1f}L average)."
        )

        return YieldDropAlert(
            animal_id=animal_id,
            baseline_yield_litres=round(baseline, 2),
            current_yield_litres=round(current, 2),
            drop_pct=round(drop_pct, 1),
            severity=severity,
            message=message,
        )
