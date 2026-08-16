import logging
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from dairyos.farm.herd.services.animal_milking_schedule_service import (
    AnimalMilkingScheduleService,
)

if TYPE_CHECKING:
    from dairyos.data.repositories.repository_factory import RepositoryFactory

logger = logging.getLogger(__name__)

SUPPORTED_PERIOD_DAYS = {
    "7d": 7,
    "30d": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
}

PERIOD_BY_DAYS = {days: period for period, days in SUPPORTED_PERIOD_DAYS.items()}


def _as_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return None


def _record_date(record, *names):
    for name in names:
        converted = _as_datetime(getattr(record, name, None))
        if converted is not None:
            return converted
    return None


def _has_entered_yield(record) -> bool:
    if getattr(record, "total_yield", None) is not None:
        return True
    return any(
        getattr(record, field, None) is not None
        for field in ("morning_yield", "afternoon_yield", "evening_yield")
    )


def resolve_period_range(
    period: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    anchor_date: Optional[date] = None,
) -> Tuple[date, date]:
    today = anchor_date or date.today()

    if period == "custom":
        if not start_date or not end_date:
            raise ValueError("custom period requires both start_date and end_date")
        if start_date > end_date:
            raise ValueError("start_date cannot be after end_date")
        return start_date, end_date

    days = SUPPORTED_PERIOD_DAYS.get(period)
    if not days:
        raise ValueError(f"unsupported period: {period}")

    return today - timedelta(days=days - 1), today


class TrendIntelligenceResult(dict):
    """Dict subclass providing .summary() compatibility."""

    def summary(self) -> Dict[str, Any]:
        return dict(self)


class MilkProductionTrendIntelligenceService:
    def __init__(
        self,
        repository_factory: Optional["RepositoryFactory"] = None,
    ):
        self._repository_factory = (
            repository_factory
            if self._looks_like_repository_factory(repository_factory)
            else None
        )
        self._compatibility_dependency = (
            None
            if self._repository_factory is not None
            else repository_factory
        )
        self._schedule_service = AnimalMilkingScheduleService()
    @staticmethod
    def _looks_like_repository_factory(value) -> bool:
        if value is None:
            return False

        return (
            hasattr(value, "session")
            and hasattr(value, "animal")
            and hasattr(value, "milk")
            and hasattr(value, "close")
        )

    def _get_factory(self) -> "RepositoryFactory":
        if self._repository_factory is not None:
            return self._repository_factory

        from dairyos.data.repositories.repository_factory import RepositoryFactory

        return RepositoryFactory.create()

    def milk(self):
        return self._get_factory().milk()
    @staticmethod
    def _record_session_values(record):
        """Return entered session yields without treating NULL as zero."""
        values = {}

        for session, field in (
            ("MORNING", "morning_yield"),
            ("AFTERNOON", "afternoon_yield"),
            ("EVENING", "evening_yield"),
        ):
            value = getattr(record, field, None)
            if value is not None:
                values[session] = float(value)

        if values:
            return values

        total = getattr(record, "total_yield", None)
        declared_session = str(
            getattr(record, "milking_session", "") or ""
        ).upper()

        if total is not None and declared_session:
            return {declared_session: float(total)}

        return {}

    def _daily_animal_snapshot(
        self,
        records,
        animal,
        histories,
        target_date,
    ):
        animal_id = str(getattr(animal, "animal_id", ""))
        frequency = self._schedule_service.get_frequency_for_date(
            animal,
            target_date,
            history=histories,
        )
        expected = self._schedule_service.get_expected_sessions(
            animal,
            target_date,
            history=histories,
        )

        if not expected:
            return None

        entered = {session: [] for session in expected}

        for record in records:
            if str(getattr(record, "animal_id", "")) != animal_id:
                continue

            timestamp = _record_date(
                record,
                "production_date",
                "recorded_at",
            )

            if timestamp is None or timestamp.date() != target_date:
                continue

            if not bool(getattr(record, "session_ledger", False)):
                continue

            status = str(
                getattr(record, "status", "") or ""
            ).upper()

            if status == "NOT_MILKED":
                continue

            for session, value in self._record_session_values(record).items():
                if session in entered:
                    entered[session].append(value)

        missing = [
            session
            for session in expected
            if not entered[session]
        ]

        if missing:
            return {
                "date": target_date.isoformat(),
                "animal_id": animal_id,
                "frequency": frequency,
                "complete": False,
                "missing_sessions": missing,
                "total_litres": None,
            }

        total = sum(
            sum(values)
            for values in entered.values()
        )

        return {
            "date": target_date.isoformat(),
            "animal_id": animal_id,
            "frequency": frequency,
            "complete": True,
            "missing_sessions": [],
            "total_litres": round(total, 2),
        }

    def _animal_histories(self, factory, animals):
        result = {}
        repo = factory.animal()

        for animal in animals:
            animal_id = str(getattr(animal, "animal_id", ""))

            try:
                result[animal_id] = repo.get_milking_frequency_history(
                    animal_id
                )
            except AttributeError:
                result[animal_id] = []

        return result

    def _complete_daily_totals(
        self,
        records,
        animals,
        histories_by_animal,
        start_date,
        end_date,
    ):
        daily_totals = {}

        current = start_date

        while current <= end_date:
            complete_animals = []

            for animal in animals:
                animal_id = str(
                    getattr(animal, "animal_id", "")
                )

                snapshot = self._daily_animal_snapshot(
                    records,
                    animal,
                    histories_by_animal.get(animal_id, []),
                    current,
                )

                if snapshot and snapshot["complete"]:
                    complete_animals.append(snapshot)

            if complete_animals:
                daily_totals[current] = round(
                    sum(
                        item["total_litres"]
                        for item in complete_animals
                    ),
                    2,
                )

            current += timedelta(days=1)

        return daily_totals
    @staticmethod
    def _eligible_animals(factory):
        return [
            animal
            for animal in factory.animal().get_all()
            if bool(getattr(animal, "active", True))
        ]

    def generate(
        self,
        operational_state: Any = None,
        as_of_date: Optional[date] = None,
        period_days: int = 7,
        **kwargs: Any,
    ) -> TrendIntelligenceResult:
        target_date = as_of_date or date.today()

        if isinstance(target_date, datetime):
            target_date = target_date.date()

        period = PERIOD_BY_DAYS.get(period_days)

        if period is None:
            raise ValueError(
                f"unsupported period_days: {period_days}"
            )

        factory = self._get_factory()
        owns_factory = self._repository_factory is None

        try:
            records = factory.milk().get_all()
            animals = self._eligible_animals(factory)
            histories = self._animal_histories(
                factory,
                animals,
            )

            start = target_date - timedelta(
                days=period_days - 1
            )

            daily_totals = self._complete_daily_totals(
                records,
                animals,
                histories,
                start,
                target_date,
            )

            current_total = daily_totals.get(target_date)

            prior_dates = [
                day
                for day in daily_totals
                if day < target_date
            ]
            prior_date = (
                max(prior_dates)
                if prior_dates
                else None
            )
            prior_total = (
                daily_totals.get(prior_date)
                if prior_date
                else None
            )

            comparison_status = (
                "COMPARED"
                if current_total is not None
                and prior_total is not None
                else "NO_COMPARISON"
            )

            variance_litres = None
            variance_percentage = None

            if comparison_status == "COMPARED":
                variance_litres = round(
                    current_total - prior_total,
                    2,
                )

                if prior_total:
                    variance_percentage = round(
                        (
                            variance_litres
                            / prior_total
                        )
                        * 100,
                        1,
                    )

            series = [
                {
                    "date": day.isoformat(),
                    "total_yield": round(
                        total,
                        2,
                    ),
                }
                for day, total in sorted(
                    daily_totals.items()
                )
            ]

            total_series = round(
                sum(
                    item["total_yield"]
                    for item in series
                ),
                2,
            )

            direction = "UNKNOWN"

            if len(series) >= 2:
                first = series[0]["total_yield"]
                last = series[-1]["total_yield"]

                direction = (
                    "INCREASING"
                    if last > first
                    else "DECREASING"
                    if last < first
                    else "STABLE"
                )

            trend = {
                "period": period,
                "start_date": start.isoformat(),
                "end_date": target_date.isoformat(),
                "series": series,
                "data_status": (
                    "LIVE_PERSISTED_DATA"
                    if series
                    else "NO_DATA"
                ),
                "total_litres": total_series,
                "daily_total": total_series,
                "total_yield": total_series,
                "complete": bool(series),
                "is_complete": bool(series),
            }

            return TrendIntelligenceResult(
                {
                    "status": "OPERATIONAL",
                    "comparison_status": comparison_status,
                    "complete": current_total is not None,
                    "is_complete": current_total is not None,
                    "daily_total": (
                        round(current_total, 2)
                        if current_total is not None
                        else None
                    ),
                    "total_litres": (
                        round(current_total, 2)
                        if current_total is not None
                        else None
                    ),
                    "total_yield": (
                        round(current_total, 2)
                        if current_total is not None
                        else None
                    ),
                    "variance_percentage": variance_percentage,
                    "variance_litres": variance_litres,
                    "records_count": len(records),
                    "prior_date": (
                        prior_date.isoformat()
                        if prior_date
                        else None
                    ),
                    "prior_total_litres": prior_total,
                    "trend_direction": direction,
                    "period_days": period_days,
                    "trend": trend,
                    "series": series,
                }
            )

        finally:
            if owns_factory:
                factory.close()

    def get_trend_analysis(
        self,
        period: str = "7d",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        anchor_date: Optional[date] = None,
        factory: Optional["RepositoryFactory"] = None,
    ) -> Dict[str, Any]:
        calc_start, calc_end = resolve_period_range(
            period=period,
            start_date=start_date,
            end_date=end_date,
            anchor_date=anchor_date,
        )

        working_factory = (
            factory
            or self._get_factory()
        )

        owns_factory = (
            factory is None
            and self._repository_factory is None
        )

        try:
            records = working_factory.milk().get_all()
            animals = self._eligible_animals(
                working_factory
            )
            histories = self._animal_histories(
                working_factory,
                animals,
            )

            daily_totals = self._complete_daily_totals(
                records,
                animals,
                histories,
                calc_start,
                calc_end,
            )

            series = [
                {
                    "date": day.isoformat(),
                    "total_yield": round(
                        total,
                        2,
                    ),
                }
                for day, total in sorted(
                    daily_totals.items()
                )
            ]

            total = round(
                sum(
                    item["total_yield"]
                    for item in series
                ),
                2,
            )

            return {
                "period": period,
                "start_date": calc_start.isoformat(),
                "end_date": calc_end.isoformat(),
                "series": series,
                "data_status": (
                    "LIVE_PERSISTED_DATA"
                    if series
                    else "NO_DATA"
                ),
                "total_litres": total,
                "daily_total": total,
                "total_yield": total,
                "complete": bool(series),
                "is_complete": bool(series),
            }

        finally:
            if owns_factory:
                working_factory.close()



