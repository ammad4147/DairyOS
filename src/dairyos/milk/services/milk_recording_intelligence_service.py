from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


class MilkRecordingIntelligenceService:
    """
    Compatibility facade for the historical /farm/milk/intelligence contract.

    The live application path must use the authoritative schedule-aware trend
    engine. This class preserves the established response shape for existing
    callers while delegating seven-day trend calculations to
    MilkProductionTrendIntelligenceService.

    Repository-only construction remains supported for legacy unit tests and
    compatibility callers that do not have a RepositoryFactory available.
    Those callers retain the historical raw-record behaviour; the production
    API supplies the RepositoryFactory and therefore uses the authoritative
    path.
    """

    def __init__(self, repository, repository_factory=None):
        self.repository = repository
        self.repository_factory = repository_factory

    @staticmethod
    def _date(value) -> date:
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if hasattr(value, "date"):
            converted = value.date()
            if isinstance(converted, date):
                return converted

        return OperationalDateAuthority().current_date()

    @staticmethod
    def _total(record) -> float:
        total = getattr(record, "total_yield", None)

        if total is not None:
            return float(total)

        return (
            float(getattr(record, "morning_yield", 0.0) or 0.0)
            + float(getattr(record, "afternoon_yield", 0.0) or 0.0)
            + float(getattr(record, "evening_yield", 0.0) or 0.0)
        )

    def records(self):
        return list(self.repository.get_all())

    def _operational_today(self) -> date:
        return OperationalDateAuthority().current_date()

    def _authoritative_trend(self, days: int = 7):
        if self.repository_factory is None:
            return None

        period = {
            7: "7d",
            30: "30d",
            90: "3mo",
            180: "6mo",
            365: "1y",
        }.get(days)

        if period is None:
            end_date = self._operational_today()
            start_date = end_date - timedelta(days=days - 1)
            return MilkProductionTrendIntelligenceService(
                repository_factory=self.repository_factory,
            ).get_trend_analysis(
                period="custom",
                start_date=start_date,
                end_date=end_date,
            )

        return MilkProductionTrendIntelligenceService(
            repository_factory=self.repository_factory,
        ).get_trend_analysis(period=period)

    def daily_totals(self, days: int = 7):
        authoritative = self._authoritative_trend(days)

        if authoritative is not None:
            series = authoritative.get("series", [])

            by_date = {
                str(item["date"]): float(
                    item.get("total_yield", 0.0) or 0.0
                )
                for item in series
            }

            end_date = self._operational_today()
            start = end_date - timedelta(days=days - 1)

            return [
                {
                    "date": (
                        start + timedelta(days=index)
                    ).isoformat(),
                    "litres": round(
                        by_date.get(
                            (
                                start + timedelta(days=index)
                            ).isoformat(),
                            0.0,
                        ),
                        2,
                    ),
                }
                for index in range(days)
            ]

        # Compatibility fallback for repository-only callers.
        end_date = self._operational_today()
        start = end_date - timedelta(days=days - 1)

        totals = defaultdict(float)

        for record in self.records():
            production_date = getattr(record, "production_date", None)

            if production_date is None:
                continue

            day = self._date(production_date)

            if start <= day <= end_date:
                totals[day.isoformat()] += self._total(record)

        return [
            {
                "date": (
                    start + timedelta(days=index)
                ).isoformat(),
                "litres": round(
                    totals[
                        (
                            start + timedelta(days=index)
                        ).isoformat()
                    ],
                    2,
                ),
            }
            for index in range(days)
        ]

    def animal_totals(self, days: int = 7):
        end_date = self._operational_today()
        start = end_date - timedelta(days=days - 1)

        totals = defaultdict(float)

        for record in self.records():
            animal_id = getattr(record, "animal_id", None)
            production_date = getattr(record, "production_date", None)

            if not animal_id or production_date is None:
                continue

            day = self._date(production_date)

            if start <= day <= end_date:
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
        daily = self.daily_totals(7)
        today = self._operational_today()
        yesterday = today - timedelta(days=1)

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
        Compatibility yield-drop presentation.

        When the live RepositoryFactory is available, daily animal values are
        reconstructed through the authoritative schedule-aware trend service.
        Incomplete animal-days are excluded from comparisons.

        The historical repository-only path remains available for compatibility.
        """

        if self.repository_factory is not None:
            trend_service = MilkProductionTrendIntelligenceService(
                repository_factory=self.repository_factory,
            )

            end_date = self._operational_today()
            start_date = end_date - timedelta(days=6)

            factory = trend_service._get_factory()

            try:
                records = factory.milk().get_all()
                animals = trend_service._eligible_animals(factory)
                histories = trend_service._animal_histories(
                    factory,
                    animals,
                )

                by_animal = {}

                for animal in animals:
                    animal_id = str(
                        getattr(
                            animal,
                            "animal_id",
                            "",
                        )
                    )

                    daily = {}

                    for day_offset in range(7):
                        target = (
                            start_date
                            + timedelta(days=day_offset)
                        )

                        snapshot = (
                            trend_service._daily_animal_snapshot(
                                records,
                                animal,
                                histories,
                                target,
                            )
                        )

                        if snapshot is None:
                            continue

                        if not snapshot.get("complete"):
                            continue

                        total = snapshot.get(
                            "total_yield"
                        )

                        if total is not None:
                            daily[target] = float(total)

                    by_animal[animal_id] = daily

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

            finally:
                if (
                    trend_service._repository_factory is None
                    and factory is not None
                ):
                    factory.close()

        # Compatibility fallback for repository-only callers.
        by_animal = defaultdict(lambda: defaultdict(float))

        for record in self.records():
            animal_id = getattr(
                record,
                "animal_id",
                None,
            )
            production_date = getattr(
                record,
                "production_date",
                None,
            )

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
