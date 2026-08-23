from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
from dairyos.finance.profitability.services.feed_opex_cost_service import FeedOpexCostService
from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    is_confirmed_pregnancy,
    is_insemination,
    is_pregnancy_check,
)


class LiveAnalyticsService:
    """Backend-owned chart/read model composed only from persisted operational evidence."""

    def build(self, days: int = 30) -> dict:
        if days < 1 or days > 365:
            raise ValueError("days must be between 1 and 365")

        operational_date = OperationalDateAuthority().current_date()
        start_date = operational_date - timedelta(days=days - 1)
        end_date_exclusive = operational_date + timedelta(days=1)
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date_exclusive, datetime.min.time(), tzinfo=timezone.utc)

        rf = RepositoryFactory.create()
        try:
            animals = [a for a in rf.animal().get_all() if getattr(a, "active", True)]
            milk_records = [
                r for r in rf.milk().get_all()
                if self._in_range(getattr(r, "production_date", None), start_date, end_date_exclusive)
            ]
            health_records = [
                r for r in rf.health().get_all()
                if self._in_range(
                    getattr(r, "observed_at", None)
                    or getattr(r, "timestamp", None)
                    or getattr(r, "observation_date", None)
                    or getattr(r, "created_at", None),
                    start_date,
                    end_date_exclusive,
                )
            ]
            treatments = [
                r for r in rf.treatment().get_all()
                if self._in_range(getattr(r, "treated_at", None), start_date, end_date_exclusive)
            ]
            breeding = [
                r for r in rf.breeding().get_all()
                if self._in_range(getattr(r, "timestamp", None), start_date, end_date_exclusive)
            ]
            finance = [
                r for r in rf.finance().get_all()
                if self._in_range(getattr(r, "transaction_date", None), start_date, end_date_exclusive)
            ]

            milk_trend = MilkProductionTrendIntelligenceService().generate(
                as_of_date=operational_date,
                period_days=days if days in {7, 30, 90, 180, 365} else 30,
            )
            milk_series = milk_trend.get("series", [])
            thi_by_date = self._thi_series(rf, start_date, end_date_exclusive)
            milk_environment = [
                {
                    "period": item["date"],
                    "thi": thi_by_date[item["date"]],
                    "yield": item["total_yield"],
                }
                for item in milk_series
                if item["date"] in thi_by_date
            ]

            health_series = self._health_series(health_records, treatments)
            breeding_series = self._breeding_series(breeding)
            cost = FeedOpexCostService().evaluate(
                milk_records,
                finance,
                days=days,
                now=end_dt,
            )

            lifecycle_counts = defaultdict(int)
            for animal in animals:
                lifecycle_counts[str(getattr(animal, "lifecycle_status", "UNKNOWN") or "UNKNOWN").upper()] += 1

            return {
                "status": "OPERATIONAL",
                "data_status": "LIVE_PERSISTED_DATA" if any(
                    (milk_series, health_series, breeding_series, finance, animals, thi_by_date)
                ) else "NO_DATA",
                "synthetic_values": False,
                "frontend_calculation_authority": False,
                "period": {
                    "start": start_date.isoformat(),
                    "end": operational_date.isoformat(),
                    "days": days,
                },
                "milk_environment": milk_environment,
                "health": health_series,
                "breeding": breeding_series,
                "financial": {
                    "feed_cost_per_litre": cost["feed_cost_per_litre"],
                    "opex_cost_per_litre": cost["opex_cost_per_litre"],
                    "cost_of_milk_production_per_litre": cost["cmpl"],
                    "feed_cost": cost["feed_cost"],
                    "opex": cost["opex"],
                    "data_status": "LIVE_PERSISTED_DATA" if finance or milk_records else "NO_DATA",
                },
                "herd_dynamics": {
                    "active_herd": len(animals),
                    "lifecycle_counts": dict(sorted(lifecycle_counts.items())),
                },
                "heat_stress": {
                    "observations": [
                        {"period": key, "thi": value}
                        for key, value in sorted(thi_by_date.items())
                    ],
                    "data_status": "LIVE_PERSISTED_DATA" if thi_by_date else "NO_DATA",
                },
                "coverage": {
                    "milk_environment_joined_days": len(milk_environment),
                    "health_days": len(health_series),
                    "breeding_months": len(breeding_series),
                    "environment_days": len(thi_by_date),
                    "animals": len(animals),
                    "milk_records": len(milk_records),
                    "health_records": len(health_records),
                    "treatments": len(treatments),
                    "breeding_records": len(breeding),
                    "finance_records": len(finance),
                },
            }
        finally:
            rf.close()

    @staticmethod
    def _as_date(value) -> date | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return None

    @classmethod
    def _in_range(cls, value, start: date, end_exclusive: date) -> bool:
        converted = cls._as_date(value)
        return converted is not None and start <= converted < end_exclusive

    @staticmethod
    def _thi_series(rf, start: date, end_exclusive: date) -> dict[str, float]:
        model = (
            rf.session.query(OperationalStateModel)
            .filter(OperationalStateModel.farm_id == "DEFAULT")
            .first()
        )
        if model is None:
            return {}

        buckets: dict[str, list[float]] = defaultdict(list)
        for item in (model.state_payload or {}).get("heat_stress_observations", []):
            try:
                observed = datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00"))
                if observed.tzinfo is None:
                    observed = observed.replace(tzinfo=timezone.utc)
                day = observed.date()
                if start <= day < end_exclusive:
                    buckets[day.isoformat()].append(float(item["thi"]))
            except (KeyError, TypeError, ValueError):
                continue

        return {
            day: round(sum(values) / len(values), 2)
            for day, values in buckets.items()
            if values
        }

    @staticmethod
    def _health_series(records, treatments) -> list[dict]:
        buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"observations": 0, "treatments": 0})
        for record in records:
            day = LiveAnalyticsService._as_date(
                getattr(record, "observed_at", None)
                or getattr(record, "timestamp", None)
                or getattr(record, "observation_date", None)
                or getattr(record, "created_at", None)
            )
            if day:
                buckets[day.isoformat()]["observations"] += 1
        for record in treatments:
            day = LiveAnalyticsService._as_date(getattr(record, "treated_at", None))
            if day:
                buckets[day.isoformat()]["treatments"] += 1
        return [
            {"period": day, **values}
            for day, values in sorted(buckets.items())
        ]

    @staticmethod
    def _breeding_series(records) -> list[dict]:
        buckets: dict[str, dict[str, object]] = defaultdict(lambda: {
            "inseminations": 0,
            "pregnancy_checks": 0,
            "confirmed_pregnancies": 0,
            "conception_rate_percent": None,
            "_outcomes": [],
        })
        ordered_inseminations = sorted(
            [r for r in records if is_insemination(r)],
            key=lambda r: getattr(r, "timestamp", None) or datetime.min.replace(tzinfo=timezone.utc),
        )
        for record in records:
            timestamp = getattr(record, "timestamp", None)
            if timestamp is None:
                continue
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            key = timestamp.strftime("%Y-%m")
            bucket = buckets[key]
            if is_insemination(record):
                bucket["inseminations"] = int(bucket["inseminations"]) + 1
            if is_pregnancy_check(record):
                bucket["pregnancy_checks"] = int(bucket["pregnancy_checks"]) + 1
                candidates = [
                    service for service in ordered_inseminations
                    if service.animal_id == record.animal_id
                    and getattr(service, "timestamp", None) is not None
                    and service.timestamp <= record.timestamp
                ]
                if candidates:
                    bucket["_outcomes"].append(1 if is_confirmed_pregnancy(record) else 0)
                if is_confirmed_pregnancy(record):
                    bucket["confirmed_pregnancies"] = int(bucket["confirmed_pregnancies"]) + 1

        result = []
        for key, bucket in sorted(buckets.items()):
            outcomes = bucket.pop("_outcomes")
            bucket["conception_rate_percent"] = (
                round(sum(outcomes) / len(outcomes) * 100, 2)
                if outcomes else None
            )
            result.append({"period": key, **bucket})
        return result
