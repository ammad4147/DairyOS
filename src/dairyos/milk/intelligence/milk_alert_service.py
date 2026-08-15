"""Milk-production alert and comparison rules.

All comparisons are date-based.  A comparison is made only between a
completed date D and the immediately preceding completed date D_prev.
"""

from typing import Any, Dict, Iterable, List, Optional


class MilkAlertService:
    def __init__(
        self,
        amber_threshold_percent: float = 15.0,
        red_threshold_percent: float = 30.0,
        zero_baseline_epsilon: float = 0.01,
    ):
        self.amber_threshold_percent = float(amber_threshold_percent)
        self.red_threshold_percent = float(red_threshold_percent)
        self.zero_baseline_epsilon = float(zero_baseline_epsilon)
        if self.amber_threshold_percent < 0 or self.red_threshold_percent < self.amber_threshold_percent:
            raise ValueError("thresholds must satisfy 0 <= amber <= red")

    def missing_entry_alert(self, recorded_animals, expected_animals):
        missing = expected_animals - recorded_animals
        if missing <= 0:
            return None
        return {
            "alert": "MISSING_MILK_ENTRIES",
            "missing_animals": missing,
            "severity": "HIGH",
        }

    def production_alert(self, actual, expected):
        """Backward-compatible legacy alert using the configured Amber threshold."""
        if expected <= 0:
            return None
        deviation = (expected - actual) / expected * 100
        severity = self._severity_for_drop(max(deviation, 0.0))
        if severity is None:
            return None
        return {
            "alert": "LOW_MILK_PRODUCTION",
            "deviation_percentage": round(deviation, 2),
            "severity": severity,
        }

    def determine_completed_dates(
        self,
        daily_records: Dict[str, Dict[str, Any]],
        expected_sessions_per_day: int = 2,
    ) -> List[str]:
        """Return explicit dates whose expected milk sessions are complete.

        ``is_completed`` is authoritative when supplied. Otherwise a record is
        complete only when its session_count reaches the expected count.
        """
        completed: List[str] = []
        for date_str, record in sorted(daily_records.items()):
            if record.get("is_completed") is True:
                completed.append(date_str)
                continue
            session_count = record.get("session_count")
            if session_count is not None and session_count >= expected_sessions_per_day:
                completed.append(date_str)
        return completed

    def immediately_preceding_completed_date(
        self,
        current_date: str,
        completed_dates: Iterable[str],
    ) -> Optional[str]:
        dates = sorted(set(completed_dates))
        preceding = [date for date in dates if date < current_date]
        return preceding[-1] if preceding else None

    def _severity_for_drop(self, drop_percent: float) -> Optional[str]:
        if drop_percent >= self.red_threshold_percent:
            return "RED"
        if drop_percent >= self.amber_threshold_percent:
            return "AMBER"
        return None

    def compare_animal_yield(
        self,
        animal_id: str,
        current_yield: float,
        preceding_yield: float,
        current_date: str,
        preceding_date: str,
    ) -> Optional[Dict[str, Any]]:
        """Compare one animal's yield on two completed dates."""
        current_yield = float(current_yield)
        preceding_yield = float(preceding_yield)
        abs_change = current_yield - preceding_yield

        if preceding_yield <= self.zero_baseline_epsilon:
            pct_change = 0.0 if current_yield <= self.zero_baseline_epsilon else 100.0
        else:
            pct_change = (abs_change / preceding_yield) * 100.0

        drop_percent = -pct_change if pct_change < 0 else 0.0
        severity = self._severity_for_drop(drop_percent)
        if severity is None:
            return None

        return {
            "alert": "ANIMAL_YIELD_DROP",
            "animal_id": animal_id,
            "current_date": current_date,
            "preceding_date": preceding_date,
            "latest_date": current_date,
            "previous_date": preceding_date,
            "current_yield": round(current_yield, 2),
            "preceding_yield": round(preceding_yield, 2),
            "absolute_change": round(abs_change, 2),
            "percentage_change": round(pct_change, 2),
            "drop_percent": round(drop_percent, 2),
            "severity": severity,
            "message": (
                f"Animal {animal_id} yield dropped by {round(drop_percent, 1)}% "
                f"({round(preceding_yield, 1)}L → {round(current_yield, 1)}L) "
                f"between {preceding_date} and {current_date}."
            ),
            "passport_url": f"#page-animal-passport?animal_id={animal_id}",
        }

    def evaluate_herd_comparison(
        self,
        current_date: str,
        preceding_date: str,
        current_total_yield: float,
        preceding_total_yield: float,
    ) -> Optional[Dict[str, Any]]:
        """Compare total herd yield between two completed dates."""
        current_total_yield = float(current_total_yield)
        preceding_total_yield = float(preceding_total_yield)
        abs_change = current_total_yield - preceding_total_yield

        if preceding_total_yield <= self.zero_baseline_epsilon:
            pct_change = 0.0 if current_total_yield <= self.zero_baseline_epsilon else 100.0
        else:
            pct_change = (abs_change / preceding_total_yield) * 100.0

        drop_percent = -pct_change if pct_change < 0 else 0.0
        severity = self._severity_for_drop(drop_percent)
        if severity is None:
            return None

        return {
            "alert": "HERD_YIELD_COMPARISON",
            "current_date": current_date,
            "preceding_date": preceding_date,
            "current_total_yield": round(current_total_yield, 2),
            "preceding_total_yield": round(preceding_total_yield, 2),
            "absolute_change": round(abs_change, 2),
            "percentage_change": round(pct_change, 2),
            "drop_percent": round(drop_percent, 2),
            "severity": severity,
        }

    def missed_session_alert(
        self,
        animal_id: str,
        date: str,
        session: str,
    ) -> Dict[str, Any]:
        return {
            "alert": "MISSED_MILKING_SESSION",
            "animal_id": animal_id,
            "date": date,
            "session": session,
            "severity": "RED",
            "message": f"Milking session {session} for animal {animal_id} was not recorded for {date}.",
            "passport_url": f"#page-animal-passport?animal_id={animal_id}",
        }

    def notification_badge(self, alerts: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        """Build bell counts, deduplicating animal yield alerts by animal/date pair."""
        alerts = list(alerts)
        animal_keys = set()
        red_animals = set()
        amber_animals = set()
        missed = 0
        for alert in alerts:
            kind = alert.get("alert")
            if kind == "ANIMAL_YIELD_DROP":
                key = (alert.get("animal_id"), alert.get("current_date") or alert.get("latest_date"))
                animal_keys.add(key)
                if alert.get("severity") == "RED":
                    red_animals.add(key[0])
                elif alert.get("severity") == "AMBER":
                    amber_animals.add(key[0])
            elif kind == "MISSED_MILKING_SESSION":
                missed += 1
        return {
            "total": len(animal_keys) + missed,
            "animal_yield_drop_count": len(animal_keys),
            "red_animal_count": len(red_animals),
            "amber_animal_count": len(amber_animals),
            "missed_milking_session_count": missed,
            "has_critical": bool(red_animals or missed),
        }
