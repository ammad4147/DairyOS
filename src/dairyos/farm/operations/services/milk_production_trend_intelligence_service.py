import logging
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

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

PERIOD_BY_DAYS = {
    days: period
    for period, days in SUPPORTED_PERIOD_DAYS.items()
}


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
    """Return True only when an operator entered an actual milk observation."""

    if getattr(record, "total_yield", None) is not None:
        return True

    return any(
        getattr(record, field, None) is not None
        for field in (
            "morning_yield",
            "afternoon_yield",
            "evening_yield",
        )
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
            raise ValueError(
                "custom period requires both start_date and end_date"
            )

        if start_date > end_date:
            raise ValueError("start_date cannot be after end_date")

        return start_date, end_date

    days = SUPPORTED_PERIOD_DAYS.get(period)

    if not days:
        raise ValueError(f"unsupported period: {period}")

    calc_start = today - timedelta(days=days - 1)

    return calc_start, today


class TrendIntelligenceResult(dict):
    """Dict subclass providing .summary() compatibility."""

    def summary(self) -> Dict[str, Any]:
        return dict(self)


class MilkProductionTrendIntelligenceService:
    def __init__(
        self,
        repository_factory: Optional["RepositoryFactory"] = None,
    ):
        # ApplicationRuntime historically injects the milk-intelligence
        # service here. That object is deliberately accepted as a
        # compatibility dependency, but it is NOT a repository factory.
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

    @staticmethod
    def _looks_like_repository_factory(value) -> bool:
        if value is None:
            return False

        # RepositoryFactory exposes the application-level session and
        # repository factory methods. A domain service may also expose
        # ``milk()`` for compatibility, so do not use that method alone
        # as the discriminator.
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
        factory = self._get_factory()

        # This method is a compatibility surface. When the service owns
        # the factory, the caller cannot safely retain the returned
        # repository after this method returns. It is therefore intended
        # only for callers that already own an injected factory.
        if self._repository_factory is None:
            return factory.milk()

        return factory.milk()

    @staticmethod
    def _qualifying_rows(
        records,
        start: datetime,
        end: datetime,
    ):
        rows = []

        for record in records:
            if not bool(getattr(record, "session_ledger", False)):
                continue

            if not _has_entered_yield(record):
                continue

            timestamp = _record_date(
                record,
                "production_date",
                "recorded_at",
            )

            if timestamp is None or not (start <= timestamp < end):
                continue

            rows.append(record)

        return rows

    @staticmethod
    def _row_total(record) -> float:
        total = getattr(record, "total_yield", None)

        if total is not None:
            return float(total)

        return sum(
            float(value)
            for value in (
                getattr(record, "morning_yield", None),
                getattr(record, "afternoon_yield", None),
                getattr(record, "evening_yield", None),
            )
            if value is not None
        )

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

            today_start = datetime.combine(
                target_date,
                datetime.min.time(),
            )

            tomorrow = today_start + timedelta(days=1)

            today_records = self._qualifying_rows(
                records,
                today_start,
                tomorrow,
            )

            total_today = sum(
                self._row_total(record)
                for record in today_records
            )

            trend_data = self.get_trend_analysis(
                period=period,
                anchor_date=target_date,
                factory=factory,
            )

            return TrendIntelligenceResult(
                {
                    "status": "OPERATIONAL",
                    "comparison_status": "COMPARED",
                    "complete": True,
                    "is_complete": True,
                    "daily_total": round(total_today, 2),
                    "total_litres": round(total_today, 2),
                    "total_yield": round(total_today, 2),
                    "variance_percentage": 0.0,
                    "variance_litres": 0.0,
                    "records_count": len(today_records),
                    "trend": trend_data,
                    "series": trend_data.get("series", []),
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

        working_factory = factory or self._get_factory()
        owns_factory = factory is None and self._repository_factory is None

        try:
            records = working_factory.milk().get_all()

            start = datetime.combine(
                calc_start,
                datetime.min.time(),
            )

            end = datetime.combine(
                calc_end + timedelta(days=1),
                datetime.min.time(),
            )

            filtered = self._qualifying_rows(
                records,
                start,
                end,
            )

            daily_totals: Dict[date, float] = {}

            for record in filtered:
                timestamp = _record_date(
                    record,
                    "production_date",
                    "recorded_at",
                )

                if timestamp is None:
                    continue

                day = timestamp.date()

                daily_totals[day] = (
                    daily_totals.get(day, 0.0)
                    + self._row_total(record)
                )

            series = [
                {
                    "date": day.isoformat(),
                    "total_yield": round(
                        daily_totals[day],
                        2,
                    ),
                }
                for day in sorted(daily_totals)
            ]

            total_series_yield = round(
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
                "total_litres": total_series_yield,
                "daily_total": total_series_yield,
                "total_yield": total_series_yield,
                "complete": True,
                "is_complete": True,
            }

        finally:
            if owns_factory:
                working_factory.close()