from datetime import date, timedelta

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.operations.services.milk_production_trend_intelligence import (
    MilkProductionTrendIntelligence,
)
from dairyos.farm.production.services.milk_daily_semantics import (
    daily_total,
    is_complete,
    record_date,
)


SUPPORTED_PERIOD_DAYS = (7, 14, 30, 90, 180, 365)


class MilkProductionTrendIntelligenceService:
    """Generates a verified daily farm milk-yield series.

    The service has no ``previous_total_litres`` argument. The comparison
    reference is derived from explicit production dates. Trend analytics do
    not generate amber/red alerts; those belong to daily drop detection.
    """

    def __init__(self, milk_production_repository=None, animal_repository=None):
        self.milk_production_repository = milk_production_repository
        self.animal_repository = animal_repository

    @staticmethod
    def _frequency_on_date(animal, history, target_date: date) -> str | None:
        candidates = []
        for item in history:
            start = getattr(item, "effective_from", None)
            end = getattr(item, "effective_to", None)
            start_date = start.date() if hasattr(start, "date") else start
            end_date = end.date() if hasattr(end, "date") else end
            if start_date is not None and start_date <= target_date and (
                end_date is None or target_date <= end_date
            ):
                candidates.append(item)
        if candidates:
            candidates.sort(
                key=lambda item: getattr(item, "effective_from", None),
                reverse=True,
            )
            return candidates[0].milking_frequency
        return getattr(animal, "milking_frequency", None)

    def _repositories(self):
        if self.milk_production_repository is not None and self.animal_repository is not None:
            return self.milk_production_repository, self.animal_repository, None
        factory = RepositoryFactory.create()
        return factory.milk(), factory.animal(), factory

    def _daily_snapshot(self, target_date: date, records, animals, histories):
        rows_by_animal = {
            str(record.animal_id): record
            for record in records
            if record_date({"production_date": record.production_date}) == target_date
            and record.session_ledger is True
            and str(record.status).upper() != "NOT_MILKED"
        }

        total = 0.0
        incomplete = []
        participating = 0

        for animal in animals:
            animal_id = str(animal.animal_id)
            history = histories.get(animal_id, [])
            frequency = self._frequency_on_date(animal, history, target_date)
            row = rows_by_animal.get(animal_id)
            if frequency is None:
                continue
            participating += 1
            payload = {
                "animal_id": animal_id,
                "production_date": target_date,
                "session_ledger": bool(row.session_ledger) if row is not None else False,
                "status": getattr(row, "status", None) if row is not None else None,
                "morning_yield": getattr(row, "morning_yield", None) if row is not None else None,
                "afternoon_yield": getattr(row, "afternoon_yield", None) if row is not None else None,
                "evening_yield": getattr(row, "evening_yield", None) if row is not None else None,
                "total_yield": getattr(row, "total_yield", None) if row is not None else None,
            }
            if row is None or not is_complete(payload, frequency):
                incomplete.append({
                    "animal_id": animal_id,
                    "missing": [
                        session
                        for session in ("MORNING", "AFTERNOON", "EVENING")
                        if session in (
                            "MORNING", "AFTERNOON", "EVENING"
                        ) and payload.get({
                            "MORNING": "morning_yield",
                            "AFTERNOON": "afternoon_yield",
                            "EVENING": "evening_yield",
                        }[session]) is None
                    ],
                })
                continue
            total += daily_total(payload)

        return {
            "date": target_date.isoformat(),
            "total_litres": round(total, 3),
            "complete": participating > 0 and not incomplete,
            "participating_animals": participating,
            "incomplete_animals": incomplete,
        }

    def generate(self, as_of_date: date | None = None, period_days: int = 30):
        if period_days not in SUPPORTED_PERIOD_DAYS:
            raise ValueError(
                f"Unsupported milk trend period {period_days}; "
                f"choose one of {SUPPORTED_PERIOD_DAYS}."
            )

        reference_date = as_of_date or date.today()
        milk_repo, animal_repo, owned_factory = self._repositories()
        try:
            records = milk_repo.get_all()
            animals = animal_repo.currently_milking_animals()
            histories = {
                str(animal.animal_id): animal_repo.get_milking_frequency_history(
                    animal.animal_id
                )
                for animal in animals
            }

            snapshots = []
            for offset in range(period_days - 1, -1, -1):
                target = reference_date - timedelta(days=offset)
                snapshots.append(
                    self._daily_snapshot(
                        target,
                        records,
                        animals,
                        histories,
                    )
                )

            current = next(
                snapshot
                for snapshot in snapshots
                if snapshot["date"] == reference_date.isoformat()
            )
            prior_date = (reference_date - timedelta(days=1)).isoformat()
            prior = next(
                snapshot for snapshot in snapshots if snapshot["date"] == prior_date
            )

            comparison_status = "COMPARED" if current["complete"] and prior["complete"] else "NO_COMPARISON"
            variance = None
            percentage = None
            if comparison_status == "COMPARED":
                variance = round(current["total_litres"] - prior["total_litres"], 3)
                if prior["total_litres"] > 0:
                    percentage = round((variance / prior["total_litres"]) * 100, 1)

            complete_series = [snapshot for snapshot in snapshots if snapshot["complete"]]
            direction = "UNKNOWN"
            if len(complete_series) >= 2:
                first = complete_series[0]["total_litres"]
                last = complete_series[-1]["total_litres"]
                direction = "INCREASING" if last > first else "DECREASING" if last < first else "STABLE"

            return MilkProductionTrendIntelligence(
                reference_date=reference_date.isoformat(),
                last_date=prior_date,
                current_total_litres=current["total_litres"] if current["complete"] else None,
                last_date_total_litres=prior["total_litres"] if prior["complete"] else None,
                variance_litres=variance,
                variance_percentage=percentage,
                comparison_status=comparison_status,
                trend_direction=direction,
                period_days=period_days,
                series=snapshots,
                signals=[],
            )
        finally:
            if owned_factory is not None:
                owned_factory.close()

    def summary(self, as_of_date: date | None = None, period_days: int = 30):
        return self.generate(as_of_date=as_of_date, period_days=period_days).summary()
