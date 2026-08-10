from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone


class MilkRecordingIntelligenceService:
    """
    Read-only milk-production intelligence.

    Source of truth:
        MilkProductionRepository

    Provides:
        - yesterday production
        - seven-day average
        - daily trend
        - animal ranking
        - configurable yield-drop alerts

    Every result remains linked to animal_id.
    """

    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def _date(value) -> datetime.date:
        if isinstance(value, datetime):
            return value.date()

        if hasattr(value, "date"):
            return value.date()

        return datetime.now(timezone.utc).date()

    @staticmethod
    def _total(record) -> float:
        return float(
            getattr(record, "total_yield", 0.0)
            or (
                float(getattr(record, "morning_yield", 0.0) or 0.0)
                + float(getattr(record, "afternoon_yield", 0.0) or 0.0)
                + float(getattr(record, "evening_yield", 0.0) or 0.0)
            )
        )

    def records(self):
        return list(self.repository.get_all())

    def daily_totals(self, days: int = 7):
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=days - 1)

        totals = defaultdict(float)

        for record in self.records():
            production_date = getattr(record, "production_date", None)

            if production_date is None:
                continue

            day = self._date(production_date)

            if start <= day <= today:
                totals[day.isoformat()] += self._total(record)

        return [
            {
                "date": (start + timedelta(days=index)).isoformat(),
                "litres": round(
                    totals[(start + timedelta(days=index))],
                    2,
                ),
            }
            for index in range(days)
        ]

    def animal_totals(self, days: int = 7):
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=days - 1)

        totals = defaultdict(float)

        for record in self.records():
            animal_id = getattr(record, "animal_id", None)
            production_date = getattr(record, "production_date", None)

            if not animal_id or production_date is None:
                continue

            day = self._date(production_date)

            if start <= day <= today:
                totals[str(animal_id)] += self._total(record)

        return sorted(
            (
                {
                    "animal_id": animal_id,
                    "litres": round(litres, 2),
                }
                for animal_id, litres in totals.items()
            ),
            key=lambda row: row["litres"],
            reverse=True,
        )

    def summary(self):
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)

        daily = self.daily_totals(7)

        yesterday_litres = next(
            (
                row["litres"]
                for row in daily
                if row["date"] == yesterday.isoformat()
            ),
            0.0,
        )

        seven_day_total = sum(
            row["litres"]
            for row in daily
        )

        return {
            "yesterday_litres": round(
                yesterday_litres,
                2,
            ),
            "seven_day_average_litres": round(
                seven_day_total / 7,
                2,
            ),
            "seven_day_total_litres": round(
                seven_day_total,
                2,
            ),
            "daily_trend": daily,
            "animal_ranking": self.animal_totals(7),
        }

    def yield_drop_alerts(
        self,
        threshold_percent: float = 20.0,
    ):
        """
        Compare each animal's latest recorded daily yield with
        its previous recorded daily yield.

        A notification is emitted when the reduction meets or
        exceeds threshold_percent.
        """

        by_animal = defaultdict(lambda: defaultdict(float))

        for record in self.records():
            animal_id = getattr(record, "animal_id", None)
            production_date = getattr(record, "production_date", None)

            if not animal_id or production_date is None:
                continue

            day = self._date(production_date)
            by_animal[str(animal_id)][day] += self._total(record)

        alerts = []

        for animal_id, daily in by_animal.items():
            ordered = sorted(
                daily.items(),
                key=lambda item: item[0],
            )

            if len(ordered) < 2:
                continue

            previous_date, previous_yield = ordered[-2]
            latest_date, latest_yield = ordered[-1]

            if previous_yield <= 0:
                continue

            reduction = (
                (previous_yield - latest_yield)
                / previous_yield
                * 100
            )

            if reduction >= threshold_percent:
                alerts.append(
                    {
                        "animal_id": animal_id,
                        "previous_date": previous_date.isoformat(),
                        "previous_litres": round(
                            previous_yield,
                            2,
                        ),
                        "latest_date": latest_date.isoformat(),
                        "latest_litres": round(
                            latest_yield,
                            2,
                        ),
                        "drop_percent": round(
                            reduction,
                            1,
                        ),
                        "severity": (
                            "HIGH"
                            if reduction >= 30
                            else "MEDIUM"
                        ),
                        "message": (
                            f"{animal_id} milk yield dropped "
                            f"{reduction:.1f}% "
                            f"({previous_yield:.1f}L → "
                            f"{latest_yield:.1f}L)."
                        ),
                    }
                )

        return sorted(
            alerts,
            key=lambda row: row["drop_percent"],
            reverse=True,
        )

    def dashboard(
        self,
        threshold_percent: float = 20.0,
    ):
        result = self.summary()

        result["yield_drop_threshold_percent"] = (
            threshold_percent
        )

        result["yield_drop_alerts"] = (
            self.yield_drop_alerts(
                threshold_percent
            )
        )

        return result
