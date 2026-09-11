from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from dairyos.api.tmr import milk_litres_for_period, tmr_feed_cost_for_period
from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.finance.opex_attribution import attributed_amount
from dairyos.finance.classification.transaction_classifier import is_expense
from dairyos.data.models.semen_inventory import SemenLot, SemenStockMovement
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
from dairyos.farm.reproduction.services.breeding_cycle_analytics_service import (
    BreedingAnalyticsService,
    BreedingCycleProjectionService,
)
from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    is_confirmed_pregnancy,
    is_insemination,
    is_pregnancy_check,
)


class LiveAnalyticsService:
    """Backend-owned chart/read model composed only from persisted operational evidence."""

    def build(self, days: int = 30, repository_factory=None) -> dict:
        if days < 1 or days > 365:
            raise ValueError("days must be between 1 and 365")

        operational_date = OperationalDateAuthority(
            repository_factory=repository_factory,
        ).current_date()
        start_date = operational_date - timedelta(days=days - 1)
        end_date_exclusive = operational_date + timedelta(days=1)
        rf = repository_factory or RepositoryFactory.create()
        owns_factory = repository_factory is None
        try:
            animals = [
                a for a in rf.animal().get_all()
                if getattr(a, "active", True)
                and str(getattr(a, "status", "ACTIVE") or "ACTIVE").upper()
                not in {"SOLD", "DECEASED", "DEAD", "DISPOSED", "CULLED", "INACTIVE", "VOID"}
                and str(getattr(a, "lifecycle_status", "") or "").upper()
                not in {"SOLD", "DECEASED", "DEAD", "DISPOSED", "CULLED", "INACTIVE", "VOID"}
            ]
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
            all_breeding = list(rf.breeding().get_all() or [])
            finance = [
                r for r in rf.finance().get_all()
                if self._in_range(getattr(r, "transaction_date", None), start_date, end_date_exclusive)
            ]

            milk_service = MilkProductionTrendIntelligenceService(
                repository_factory=rf,
            )
            milk_trend = milk_service.get_trend_analysis(
                period="custom",
                start_date=start_date,
                end_date=operational_date,
                anchor_date=operational_date,
                factory=rf,
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
            health_cases = list(rf.health_cases().get_all() or [])
            health_summary = self._health_summary(
                health_cases,
                treatments,
                start_date,
                operational_date,
            )

            all_cycles = BreedingCycleProjectionService.project(all_breeding)
            cycles = [
                cycle for cycle in all_cycles
                if self._cycle_intersects_period(
                    cycle,
                    start_date,
                    operational_date,
                )
            ]
            breeding_analytics = BreedingAnalyticsService.summarize(cycles)
            breeding_series = self._breeding_cycle_series(cycles)
            # Feed Cost/L is governed by the TMR Preparation Tool's
            # whole-herd daily cost, not by whether an operator separately
            # entered a Finance FEED transaction.  The period authority uses
            # immutable daily TMR snapshots and therefore responds to the
            # selected timeframe while preserving herd/formula changes.
            tmr_cost = tmr_feed_cost_for_period(
                rf,
                start_date,
                operational_date,
            )
            tmr_litres = milk_litres_for_period(
                rf,
                start_date,
                operational_date,
            )
            raw_tmr_feed_total = tmr_cost.get("total_feed_cost")
            tmr_feed_total = (
                float(raw_tmr_feed_total)
                if raw_tmr_feed_total is not None
                and bool(tmr_cost.get("complete", True))
                else None
            )
            tmr_feed_per_litre = (
                round(float(tmr_feed_total) / tmr_litres, 4)
                if tmr_feed_total is not None and tmr_litres > 0.001
                else None
            )
            opex = self._attributed_opex(
                rf,
                start_date,
                operational_date,
            )
            opex_total = opex["total"]
            opex_per_litre = (
                round(opex_total / tmr_litres, 4)
                if tmr_litres > 0.001
                else None
            )
            total_per_litre = (
                round((float(tmr_feed_total) + opex_total) / tmr_litres, 4)
                if tmr_feed_total is not None and tmr_litres > 0.001
                else None
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
                "health_summary": health_summary,
                "breeding": breeding_series,
                "breeding_cycle_analytics": breeding_analytics,
                "financial": {
                    "feed_cost_per_litre": tmr_feed_per_litre,
                    "opex_cost_per_litre": opex_per_litre,
                    "cost_of_milk_production_per_litre": total_per_litre,
                    "feed_cost": tmr_feed_total,
                    "feed_cost_basis": tmr_cost["source"],
                    "feed_cost_complete": tmr_cost["complete"],
                    "feed_cost_missing_authority_days": tmr_cost["missing_authority_days"],
                    "opex": opex_total,
                    "unattributed_opex": opex["unattributed"],
                    "non_opex_excluded": opex["non_opex_excluded"],
                    "milk_litres": tmr_litres,
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
                    "breeding_records": len(all_breeding),
                    "finance_records": len(finance),
                },
            }
        finally:
            if owns_factory:
                rf.close()

    @staticmethod
    def _as_date(value) -> date | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                ).date()
            except ValueError:
                try:
                    return date.fromisoformat(value[:10])
                except ValueError:
                    return None
        return None

    @classmethod
    def _in_range(cls, value, start: date, end_exclusive: date) -> bool:
        converted = cls._as_date(value)
        return converted is not None and start <= converted < end_exclusive

    @classmethod
    def _cycle_intersects_period(
        cls,
        cycle: dict,
        start: date,
        end: date,
    ) -> bool:
        started = cls._as_date(cycle.get("started_at"))
        if started is None or started > end:
            return False
        outcome = cls._as_date(cycle.get("outcome_date"))
        if outcome is not None and outcome < start:
            return False
        return True

    @classmethod
    def _breeding_cycle_series(cls, cycles) -> list[dict]:
        """Return monthly chart points using one row per governed AI cycle."""
        buckets: dict[str, dict[str, object]] = defaultdict(
            lambda: {
                "inseminations": 0,
                "pregnancy_checks": 0,
                "confirmed_pregnancies": 0,
                "documented_outcomes": 0,
                "conception_rate_percent": None,
                "_cycles": [],
            }
        )
        for cycle in cycles:
            started = cls._as_date(cycle.get("started_at"))
            if started is None:
                continue
            bucket = buckets[started.strftime("%Y-%m")]
            bucket["inseminations"] = int(bucket["inseminations"]) + 1
            bucket["_cycles"].append(cycle)
            events = cycle.get("events") or []
            bucket["pregnancy_checks"] = int(bucket["pregnancy_checks"]) + sum(
                1
                for event in events
                if str(event.get("event_type") or "").lower()
                in {"pregnancy_check", "pregnancy_diagnosis", "pregnancy", "pregnancy_negative"}
            )
            if cycle.get("pregnancy_confirmation_date"):
                bucket["confirmed_pregnancies"] = int(
                    bucket["confirmed_pregnancies"]
                ) + 1

        result = []
        for key, bucket in sorted(buckets.items()):
            rows = list(bucket.pop("_cycles"))
            documented = [
                cycle for cycle in rows
                if cycle.get("pregnancy_confirmation_date")
                or cycle.get("outcome") in {
                    "NOT_PREGNANT",
                    "PREGNANCY_LOST",
                    "ABORTION",
                    "STILLBIRTH",
                    "CALVING",
                }
            ]
            bucket["documented_outcomes"] = len(documented)
            bucket["conception_rate_percent"] = (
                round(
                    sum(
                        1 for cycle in documented
                        if cycle.get("pregnancy_confirmation_date")
                    )
                    / len(documented)
                    * 100,
                    2,
                )
                if documented
                else None
            )
            result.append({"period": key, **bucket})
        return result

    @classmethod
    def _health_summary(
        cls,
        cases,
        treatments,
        start: date,
        end: date,
    ) -> dict:
        new_cases = [
            case for case in cases
            if cls._in_range(getattr(case, "opened_at", None), start, end + timedelta(days=1))
        ]
        resolved_cases = [
            case for case in cases
            if cls._in_range(getattr(case, "resolved_at", None), start, end + timedelta(days=1))
        ]
        open_cases = [
            case for case in cases
            if str(getattr(case, "status", "") or "").upper() != "RESOLVED"
            and (cls._as_date(getattr(case, "opened_at", None)) or date.min) <= end
        ]
        severity_counts: dict[str, int] = defaultdict(int)
        diagnosis_counts: dict[str, int] = defaultdict(int)
        for case in open_cases:
            severity_counts[str(getattr(case, "severity", "NORMAL") or "NORMAL").upper()] += 1
            diagnosis = str(getattr(case, "diagnosis", "Unspecified") or "Unspecified").strip()
            diagnosis_counts[diagnosis] += 1

        withdrawal_animals: set[str] = set()
        withdrawal_days = 0
        for treatment in treatments:
            until = cls._as_date(getattr(treatment, "milk_withdrawal_until", None))
            if until is None or until < start:
                continue
            treatment_day = cls._as_date(getattr(treatment, "treated_at", None)) or start
            overlap_start = max(start, treatment_day)
            overlap_end = min(end, until)
            if overlap_end >= overlap_start:
                withdrawal_days += (overlap_end - overlap_start).days + 1
                animal_id = str(getattr(treatment, "animal_id", "") or "").strip()
                if animal_id:
                    withdrawal_animals.add(animal_id)

        return {
            "new_cases": len(new_cases),
            "resolved_cases": len(resolved_cases),
            "open_cases": len(open_cases),
            "open_cases_by_severity": dict(sorted(severity_counts.items())),
            "open_cases_by_diagnosis": [
                {"diagnosis": key, "count": value}
                for key, value in sorted(
                    diagnosis_counts.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ],
            "treatments": len(treatments),
            "withdrawal_animals": len(withdrawal_animals),
            "withdrawal_days": withdrawal_days,
            "data_status": "LIVE_PERSISTED_DATA" if cases or treatments else "NO_DATA",
        }

    @staticmethod
    def _attributed_opex(factory, start: date, end: date) -> dict[str, float]:
        """Reuse the governed Finance OPEX attribution policy for Analytics."""
        total = 0.0
        unattributed = 0.0
        non_opex_excluded = 0.0
        for item in factory.finance().get_all() or []:
            status = str(getattr(item, "status", "") or "").strip().upper()
            if status == "VOID" or not is_expense(item):
                continue
            master = str(getattr(item, "master_category", "") or "").strip().upper()
            if master != "OPEX":
                continue
            amount = float(getattr(item, "amount", 0.0) or 0.0)
            if amount <= 0:
                continue
            attributed, attribution_status = attributed_amount(item, start, end)

            if (
                attribution_status == "UNATTRIBUTED"
                and str(getattr(item, "cop_attribution_method", "") or "").upper() == "CONSUMPTION"
                and str(getattr(item, "sub_category", "") or "").strip()
                == "Semen Straws (Sexed / Conventional)"
            ):
                lot = (
                    factory.session.query(SemenLot)
                    .filter(SemenLot.purchase_transaction_id == item.id)
                    .first()
                )
                if lot is not None:
                    used_quantity = sum(
                        abs(int(movement.signed_quantity or 0))
                        for movement in factory.session.query(SemenStockMovement).filter(
                            SemenStockMovement.semen_lot_id == lot.id,
                            SemenStockMovement.signed_quantity < 0,
                        ).all()
                        if getattr(movement, "recorded_at", None) is not None
                        and start <= movement.recorded_at.date() <= end
                    )
                    if used_quantity > 0:
                        attributed = float(lot.unit_cost or 0.0) * used_quantity
                        attribution_status = "ATTRIBUTED"

            if attribution_status == "ATTRIBUTED":
                total += float(attributed)
            elif attribution_status == "UNATTRIBUTED":
                unattributed += amount
            elif attribution_status == "NON_OPEX":
                non_opex_excluded += amount

        return {
            "total": round(total, 2),
            "unattributed": round(unattributed, 2),
            "non_opex_excluded": round(non_opex_excluded, 2),
        }

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
