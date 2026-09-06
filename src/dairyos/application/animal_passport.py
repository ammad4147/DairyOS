"""Authoritative lifetime-biological Animal Passport read model.

The Passport remains projection-only. Persisted domain records remain the
source of truth; this service assembles a single animal-centric biological
record containing identity, recursive lineage, production/lactation history,
reproductive lifecycle, health cases, active milk withdrawal state, and the
existing operational history.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Iterable

from dairyos.core.time_utils import utcnow
from dairyos.farm.herd.services.animal_milking_schedule_service import (
    AnimalMilkingScheduleService,
)
from dairyos.farm.reproduction.services.reproductive_state_service import (
    ReproductivePolicy,
    ReproductiveStateService,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


_REPRODUCTIVE_POLICY = ReproductivePolicy(
    voluntary_waiting_period_days=60,
    gestation_days=283,
    dry_off_days_before_calving=60,
)


class LifetimeAnimalPassportService:
    """Project persisted animal-domain records into one biological passport."""

    MAX_LINEAGE_DEPTH = 20

    def __init__(self, repository_factory):
        self.factory = repository_factory
        self.schedule_service = AnimalMilkingScheduleService()

    @staticmethod
    def _serialize(record: Any) -> dict[str, Any]:
        if isinstance(record, dict):
            values = dict(record)
        elif hasattr(record, "__dict__"):
            values = {
                key: value
                for key, value in vars(record).items()
                if not key.startswith("_")
            }
        else:
            values = {"value": str(record)}

        for key, value in list(values.items()):
            if isinstance(value, (datetime, date)):
                values[key] = value.isoformat()
        return values

    @staticmethod
    def _for_animal(records: Iterable[Any], animal_id: str) -> list[Any]:
        return [
            record
            for record in records
            if str(getattr(record, "animal_id", "")) == animal_id
        ]

    @staticmethod
    def _record_date(record: Any) -> date | None:
        for key in (
            "production_date",
            "observation_date",
            "observed_at",
            "feeding_date",
            "transaction_date",
            "treated_at",
            "opened_at",
            "event_date",
            "timestamp",
            "created_at",
            "updated_at",
        ):
            value = getattr(record, key, None)
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, date):
                return value
            if value:
                try:
                    return datetime.fromisoformat(str(value)).date()
                except ValueError:
                    continue
        return None

    @classmethod
    def _through_date(
        cls,
        records: Iterable[Any],
        as_of_date: date | None,
    ) -> list[Any]:
        records = list(records)
        if as_of_date is None:
            return records
        return [
            record
            for record in records
            if (
                record_date := cls._record_date(record)
            ) is not None
            and record_date <= as_of_date
        ]

    @staticmethod
    def _record_timestamp(record: dict[str, Any]) -> Any:
        for key in (
            "production_date",
            "observation_date",
            "observed_at",
            "feeding_date",
            "transaction_date",
            "treated_at",
            "opened_at",
            "event_date",
            "timestamp",
            "created_at",
            "updated_at",
        ):
            value = record.get(key)
            if value:
                return value
        return ""

    @staticmethod
    def _event_for_animal(event: Any, animal_id: str) -> bool:
        description = str(getattr(event, "description", ""))
        return (
            f"entity_id={animal_id}" in description
            or f"animal_id={animal_id}" in description
        )

    @staticmethod
    def _animal_identity(animal: Any) -> dict[str, Any]:
        return {
            "id": animal.id,
            "animal_id": animal.animal_id,
            "animal_type": animal.animal_type,
            "ear_tag": animal.ear_tag,
            "rfid": animal.rfid,
            "breed": animal.breed,
            "sex": animal.sex,
            "date_of_birth": (
                animal.date_of_birth.isoformat()
                if animal.date_of_birth
                else None
            ),
            "dam_id": getattr(animal, "dam_id", None),
            "sire_id": getattr(animal, "sire_id", None),
            "lifecycle_status": animal.lifecycle_status,
            "status": animal.status,
            "is_currently_milking": getattr(animal, "is_currently_milking", False),
            "milking_frequency": getattr(animal, "milking_frequency", None),
            "production_group": getattr(animal, "production_group", None),
            "location": getattr(animal, "location", None),
            "active": animal.active,
            "non_milking_directive": getattr(animal, "non_milking_directive", None),
            "non_milking_reason": getattr(animal, "non_milking_reason", None),
            "created_at": (
                animal.created_at.isoformat()
                if getattr(animal, "created_at", None)
                else None
            ),
            "updated_at": (
                animal.updated_at.isoformat()
                if getattr(animal, "updated_at", None)
                else None
            ),
        }

    @staticmethod
    def _parent_snapshot(parent: Any, relation: str) -> dict[str, Any]:
        if parent is None:
            return {
                "relation": relation,
                "animal_id": None,
                "status": "UNKNOWN",
            }
        return {
            "relation": relation,
            "animal_id": parent.animal_id,
            "ear_tag": getattr(parent, "ear_tag", None),
            "rfid": getattr(parent, "rfid", None),
            "animal_type": getattr(parent, "animal_type", None),
            "sex": getattr(parent, "sex", None),
            "breed": getattr(parent, "breed", None),
            "date_of_birth": (
                parent.date_of_birth.isoformat()
                if getattr(parent, "date_of_birth", None)
                else None
            ),
            "status": getattr(parent, "status", None),
            "lifecycle_status": getattr(parent, "lifecycle_status", None),
        }

    def _lineage_projection(
        self,
        animal: Any,
        animals: list[Any],
    ) -> dict[str, Any]:
        by_id = {
            str(item.animal_id): item
            for item in animals
            if getattr(item, "animal_id", None)
        }
        children_by_parent: dict[str, list[Any]] = defaultdict(list)
        for item in animals:
            dam_id = getattr(item, "dam_id", None)
            sire_id = getattr(item, "sire_id", None)
            if dam_id:
                children_by_parent[str(dam_id)].append(item)
            if sire_id:
                children_by_parent[str(sire_id)].append(item)

        broken_links: list[dict[str, Any]] = []
        for item in animals:
            for relation, parent_id in (
                ("dam", getattr(item, "dam_id", None)),
                ("sire", getattr(item, "sire_id", None)),
            ):
                if parent_id and str(parent_id) not in by_id:
                    broken_links.append(
                        {
                            "animal_id": item.animal_id,
                            "relation": relation,
                            "referenced_id": str(parent_id),
                        }
                    )

        parent_nodes = []
        for relation, parent_id in (
            ("dam", getattr(animal, "dam_id", None)),
            ("sire", getattr(animal, "sire_id", None)),
        ):
            parent = by_id.get(str(parent_id)) if parent_id else None
            node = self._parent_snapshot(parent, relation)
            if parent_id and parent is None:
                node["status"] = "BROKEN_LINK"
            parent_nodes.append(node)

        ancestors: list[dict[str, Any]] = []
        ancestor_cycles: list[str] = []

        def walk_ancestors(current_id: str, depth: int, path: set[str]) -> None:
            if depth > self.MAX_LINEAGE_DEPTH:
                return
            current = by_id.get(current_id)
            if current is None:
                return
            for relation, parent_id in (
                ("dam", getattr(current, "dam_id", None)),
                ("sire", getattr(current, "sire_id", None)),
            ):
                if not parent_id:
                    continue
                parent_key = str(parent_id)
                if parent_key in path:
                    ancestor_cycles.append(parent_key)
                    continue
                parent = by_id.get(parent_key)
                ancestors.append(
                    {
                        "depth": depth,
                        "relation": relation,
                        "animal_id": parent_key,
                        "ear_tag": getattr(parent, "ear_tag", None) if parent else None,
                        "animal_type": getattr(parent, "animal_type", None) if parent else None,
                        "breed": getattr(parent, "breed", None) if parent else None,
                        "status": getattr(parent, "status", None) if parent else "BROKEN_LINK",
                    }
                )
                if parent is not None:
                    walk_ancestors(parent_key, depth + 1, path | {parent_key})

        walk_ancestors(animal.animal_id, 1, {animal.animal_id})

        descendants: list[dict[str, Any]] = []
        descendant_cycles: list[str] = []
        seen_descendants: set[tuple[str, str]] = set()

        def walk_descendants(parent_id: str, depth: int, path: set[str]) -> None:
            if depth > self.MAX_LINEAGE_DEPTH:
                return
            for child in children_by_parent.get(parent_id, []):
                child_id = str(child.animal_id)
                marker = (parent_id, child_id)
                if marker in seen_descendants:
                    continue
                seen_descendants.add(marker)
                relation = (
                    "dam_child"
                    if str(getattr(child, "dam_id", "")) == parent_id
                    else "sire_child"
                )
                if child_id in path:
                    descendant_cycles.append(child_id)
                    continue
                descendants.append(
                    {
                        "depth": depth,
                        "relation": relation,
                        "animal_id": child_id,
                        "ear_tag": getattr(child, "ear_tag", None),
                        "animal_type": getattr(child, "animal_type", None),
                        "sex": getattr(child, "sex", None),
                        "breed": getattr(child, "breed", None),
                        "date_of_birth": (
                            child.date_of_birth.isoformat()
                            if getattr(child, "date_of_birth", None)
                            else None
                        ),
                        "lifecycle_status": getattr(child, "lifecycle_status", None),
                        "status": getattr(child, "status", None),
                        "is_currently_milking": getattr(child, "is_currently_milking", False),
                    }
                )
                walk_descendants(child_id, depth + 1, path | {child_id})

        walk_descendants(animal.animal_id, 1, {animal.animal_id})
        ancestors.sort(key=lambda item: (item["depth"], item["animal_id"]))
        descendants.sort(key=lambda item: (item["depth"], item["animal_id"]))

        return {
            "parents": parent_nodes,
            "ancestors": ancestors,
            "descendants": descendants,
            "integrity": {
                "broken_parent_links": broken_links,
                "ancestor_cycles": sorted(set(ancestor_cycles)),
                "descendant_cycles": sorted(set(descendant_cycles)),
                "max_depth": self.MAX_LINEAGE_DEPTH,
                "known_ancestor_count": len(ancestors),
                "known_descendant_count": len(descendants),
            },
        }

    @staticmethod
    def _milk_total(record: Any) -> float:
        total = getattr(record, "total_yield", None)
        if total is not None:
            return float(total)
        values = [
            getattr(record, "morning_yield", None),
            getattr(record, "afternoon_yield", None),
            getattr(record, "evening_yield", None),
        ]
        return float(sum(value for value in values if value is not None))

    def _lactation_projection(
        self,
        milk: list[Any],
        breeding: list[Any],
        as_of_date: date,
    ) -> dict[str, Any]:
        calving_dates = sorted(
            {
                record_date
                for record in breeding
                if (
                    record_date := self._record_date(record)
                ) is not None
                and self._normalize_breeding_event_type(
                    getattr(record, "event_type", "")
                ) == "CALVING"
                and record_date <= as_of_date
            }
        )

        daily_totals: dict[date, float] = defaultdict(float)
        for record in milk:
            record_date = self._record_date(record)
            if record_date is None or record_date > as_of_date:
                continue
            daily_totals[record_date] += self._milk_total(record)

        lifetime_total = round(sum(daily_totals.values()), 3)
        recorded_days = len(daily_totals)
        peak_date = max(daily_totals, key=daily_totals.get) if daily_totals else None
        peak_yield = daily_totals.get(peak_date) if peak_date else None

        lactations: list[dict[str, Any]] = []
        for index, start_date in enumerate(calving_dates, start=1):
            next_calving = calving_dates[index] if index < len(calving_dates) else None
            end_date = next_calving - timedelta(days=1) if next_calving else None
            entries = {
                day: value
                for day, value in daily_totals.items()
                if day >= start_date
                and (next_calving is None or day < next_calving)
            }
            milk_total = round(sum(entries.values()), 3)
            local_peak_date = max(entries, key=entries.get) if entries else None
            current = next_calving is None
            lactations.append(
                {
                    "lactation_number": index,
                    "calving_date": start_date.isoformat(),
                    "end_date": end_date.isoformat() if end_date else None,
                    "status": "CURRENT" if current else "COMPLETED",
                    "days_in_lactation": (
                        (as_of_date - start_date).days
                        if current
                        else (next_calving - start_date).days
                    ),
                    "milk_liters": milk_total,
                    "recorded_days": len(entries),
                    "average_liters_per_recorded_day": (
                        round(milk_total / len(entries), 3)
                        if entries
                        else 0.0
                    ),
                    "peak_daily_yield_liters": (
                        round(entries[local_peak_date], 3)
                        if local_peak_date
                        else None
                    ),
                    "peak_daily_yield_date": (
                        local_peak_date.isoformat()
                        if local_peak_date
                        else None
                    ),
                }
            )

        lifetime = {
            "lactation_count": len(lactations),
            "lifetime_milk_liters": lifetime_total,
            "recorded_milk_days": recorded_days,
            "average_liters_per_recorded_day": (
                round(lifetime_total / recorded_days, 3)
                if recorded_days
                else 0.0
            ),
            "peak_daily_yield_liters": (
                round(peak_yield, 3) if peak_yield is not None else None
            ),
            "peak_daily_yield_date": (
                peak_date.isoformat() if peak_date else None
            ),
            "latest_milk_date": (
                max(daily_totals).isoformat() if daily_totals else None
            ),
            "daily_totals_considered": len(daily_totals),
        }

        monthly_buckets: dict[str, dict[date, float]] = defaultdict(dict)
        for production_date, litres in daily_totals.items():
            month_key = production_date.strftime("%Y-%m")
            monthly_buckets[month_key][production_date] = litres

        monthly_output: list[dict[str, Any]] = []
        for month_key in sorted(monthly_buckets, reverse=True):
            entries = monthly_buckets[month_key]
            month_total = round(sum(entries.values()), 3)
            month_peak_date = max(entries, key=entries.get) if entries else None
            monthly_output.append(
                {
                    "month": month_key,
                    "milk_liters": month_total,
                    "recorded_days": len(entries),
                    "average_liters_per_recorded_day": (
                        round(month_total / len(entries), 3)
                        if entries
                        else 0.0
                    ),
                    "peak_daily_yield_liters": (
                        round(entries[month_peak_date], 3)
                        if month_peak_date
                        else None
                    ),
                    "peak_daily_yield_date": (
                        month_peak_date.isoformat()
                        if month_peak_date
                        else None
                    ),
                }
            )

        return {
            "lactations": lactations,
            "monthly_output": monthly_output,
            "lifetime": lifetime,
            "summary": dict(lifetime),
        }

    @staticmethod
    def _normalize_breeding_event_type(value: Any) -> str:
        raw = str(value or "").strip().lower()
        if raw in {"insemination", "service", "ai", "artificial_insemination"}:
            return "INSEMINATION"
        if raw == "pregnancy_negative":
            return "PREGNANCY_NEGATIVE"
        if raw in {"pregnancy_check", "pregnancy_diagnosis", "pregnancy"}:
            return "PREGNANCY_CONFIRMED"
        if raw == "pregnancy_confirmed":
            return "PREGNANCY_CONFIRMED"
        if raw in {"calving", "calved", "parturition"}:
            return "CALVING"
        if raw == "dry_off":
            return "DRY_OFF"
        return ""

    def _reproductive_projection(
        self,
        animal_id: str,
        breeding: list[Any],
        as_of_date: date,
    ) -> dict[str, Any]:
        events: list[dict[str, Any]] = []
        for record in breeding:
            event_date = self._record_date(record)
            normalized = self._normalize_breeding_event_type(
                getattr(record, "event_type", "")
            )
            if event_date is None or event_date > as_of_date or not normalized:
                continue
            raw_timestamp = getattr(record, "timestamp", None)

            if isinstance(raw_timestamp, datetime):
                event_timestamp = raw_timestamp.isoformat()
            elif isinstance(raw_timestamp, date):
                event_timestamp = datetime.combine(
                    raw_timestamp,
                    datetime.min.time(),
                ).isoformat()
            elif raw_timestamp:
                event_timestamp = str(raw_timestamp)
            else:
                event_timestamp = ""

            events.append(
                {
                    "animal_id": animal_id,
                    "event_type": normalized,
                    "event_date": event_date,
                    "timestamp": event_timestamp,
                    "result": getattr(record, "result", None),
                    "technician": getattr(record, "technician", None),
                    "record_id": getattr(record, "record_id", None),
                }
            )
        events.sort(
            key=lambda item: (
                item["event_date"],
                item["timestamp"],
                item["record_id"] or "",
            )
        )
        resolver = ReproductiveStateService(_REPRODUCTIVE_POLICY)
        state = resolver.resolve(
            animal_id,
            events,
            as_of_date=as_of_date,
            allow_unlinked_confirmation=True,
        )
        summary = {
            "current_status": state.reproductive_status,
            "current_api_status": self._current_reproductive_api_value(state),
            "pregnancy_status": state.pregnancy_status,
            "lactation_number": state.lactation_number,
            "days_in_milk": state.days_in_milk,
            "last_calving_date": (
                state.last_calving_date.isoformat()
                if state.last_calving_date
                else None
            ),
            "last_insemination_date": (
                state.last_insemination_date.isoformat()
                if state.last_insemination_date
                else None
            ),
            "pregnancy_confirmed_date": (
                state.pregnancy_confirmed_date.isoformat()
                if state.pregnancy_confirmed_date
                else None
            ),
            "expected_calving_date": (
                state.expected_calving_date.isoformat()
                if state.expected_calving_date
                else None
            ),
            "eligible_to_breed": state.eligible_to_breed,
            "days_open": state.days_open,
            "expected_dry_off_date": (
                state.expected_dry_off_date.isoformat()
                if state.expected_dry_off_date
                else None
            ),
            "dry_period_status": state.dry_period_status,
            "lifetime_calvings": sum(
                event["event_type"] == "CALVING" for event in events
            ),
            "lifetime_inseminations": sum(
                event["event_type"] == "INSEMINATION" for event in events
            ),
            "pregnancy_confirmations": sum(
                event["event_type"] == "PREGNANCY_CONFIRMED" for event in events
            ),
            "pregnancy_losses_or_negative_checks": sum(
                event["event_type"] == "PREGNANCY_NEGATIVE" for event in events
            ),
            "dry_off_events": sum(
                event["event_type"] == "DRY_OFF" for event in events
            ),
        }
        lifecycle = [
            {
                "event_date": item["event_date"].isoformat(),
                "event_type": item["event_type"],
                "result": item["result"],
                "technician": item["technician"],
                "record_id": item["record_id"],
            }
            for item in reversed(events)
        ]
        return {"summary": summary, "events": lifecycle}

    @staticmethod
    def _current_reproductive_api_value(state: Any) -> str:
        if (
            getattr(state, "last_calving_date", None) is not None
            and state.last_calving_date == state.as_of_date
        ):
            return "CALVED"
        if getattr(state, "pregnancy_status", None) == "PREGNANT":
            return "PREGNANT"
        if getattr(state, "reproductive_status", None) == "BRED":
            return "INSEMINATED"
        if getattr(state, "reproductive_status", None) == "LACTATING":
            return "LACTATING"
        return "OPEN"

    def _health_projection(
        self,
        animal_id: str,
        as_of_date: date,
        treatments: list[Any] | None = None,
    ) -> dict[str, Any]:
        observations = self._for_animal(
            self._through_date(self.factory.health().get_all(), as_of_date),
            animal_id,
        )
        cases = self._through_date(
            self.factory.health_cases().get_by_animal(animal_id),
            as_of_date,
        )
        if treatments is None:
            treatments = self._through_date(
                self.factory.treatment().get_by_animal(animal_id),
                as_of_date,
            )
        open_cases = [
            case
            for case in cases
            if str(getattr(case, "status", "")).upper() == "OPEN"
        ]

        active_withdrawals: list[dict[str, Any]] = []
        for treatment in treatments:
            withdrawal_until = getattr(treatment, "milk_withdrawal_until", None)
            withdrawal_date = (
                withdrawal_until.date()
                if isinstance(withdrawal_until, datetime)
                else withdrawal_until
            )
            if withdrawal_date is not None and withdrawal_date >= as_of_date:
                active_withdrawals.append(
                    {
                        "source": "TREATMENT",
                        "treatment_id": getattr(treatment, "id", None),
                        "medicine": getattr(treatment, "medicine", None),
                        "withdrawal_until": withdrawal_date.isoformat(),
                        "withdrawal_source": getattr(
                            treatment, "withdrawal_source", None
                        ),
                    }
                )

        latest_observation = (
            max(
                observations,
                key=lambda item: self._record_date(item) or date.min,
            )
            if observations
            else None
        )
        clinical_log: list[dict[str, Any]] = []
        for observation in observations:
            clinical_log.append(
                {
                    "event_type": "CLINICAL_OBSERVATION",
                    "event_date": (
                        self._record_date(observation).isoformat()
                        if self._record_date(observation)
                        else None
                    ),
                    "status": getattr(observation, "status", None) or "LOGGED",
                    "detail": (
                        getattr(observation, "observation", None)
                        or getattr(observation, "symptom", None)
                    ),
                    "severity": getattr(observation, "severity", None),
                    "record_id": getattr(observation, "id", None),
                }
            )
        for case in cases:
            clinical_log.append(
                {
                    "event_type": "HEALTH_CASE",
                    "event_date": (
                        self._record_date(case).isoformat()
                        if self._record_date(case)
                        else None
                    ),
                    "status": getattr(case, "status", None),
                    "detail": (
                        getattr(case, "diagnosis", None)
                        or getattr(case, "notes", None)
                    ),
                    "severity": getattr(case, "severity", None),
                    "record_id": getattr(case, "case_id", None),
                }
            )
        for treatment in treatments:
            clinical_log.append(
                {
                    "event_type": "TREATMENT",
                    "event_date": (
                        self._record_date(treatment).isoformat()
                        if self._record_date(treatment)
                        else None
                    ),
                    "status": "RECORDED",
                    "detail": getattr(treatment, "diagnosis", None),
                    "medicine": getattr(treatment, "medicine", None),
                    "record_id": getattr(treatment, "id", None),
                }
            )
        clinical_log.sort(
            key=lambda item: str(item.get("event_date") or ""),
            reverse=True,
        )
        return {
            "summary": {
                "open_case_count": len(open_cases),
                "observation_count": len(observations),
                "treatment_count": len(treatments),
                "active_withdrawal": bool(active_withdrawals),
                "latest_observation_date": (
                    self._record_date(latest_observation).isoformat()
                    if latest_observation and self._record_date(latest_observation)
                    else None
                ),
                "latest_observation": (
                    (
                        getattr(latest_observation, "observation", None)
                        or getattr(latest_observation, "symptom", None)
                    )
                    if latest_observation
                    else None
                ),
            },
            "open_cases": [
                {
                    "case_id": getattr(case, "case_id", None),
                    "severity": getattr(case, "severity", None),
                    "diagnosis": getattr(case, "diagnosis", None),
                    "status": getattr(case, "status", None),
                    "opened_at": (
                        getattr(case, "opened_at", None).isoformat()
                        if getattr(case, "opened_at", None)
                        else None
                    ),
                    "follow_up_due_at": (
                        getattr(case, "follow_up_due_at", None).isoformat()
                        if getattr(case, "follow_up_due_at", None)
                        else None
                    ),
                    "withdrawal_until": (
                        getattr(case, "withdrawal_until", None).isoformat()
                        if getattr(case, "withdrawal_until", None)
                        else None
                    ),
                    "resolution": getattr(case, "resolution", None),
                }
                for case in open_cases
            ],
            "clinical_log": clinical_log,
            "active_withdrawals": active_withdrawals,
        }

    def _schedule_projection(self, animal: Any, as_of_date: date | None) -> dict[str, Any]:
        history = list(
            self.factory.animal().get_milking_frequency_history(animal.animal_id)
        )
        if as_of_date is None:
            snapshot = self.schedule_service.get_schedule_snapshot(animal)
        else:
            snapshot = self.schedule_service.get_schedule_snapshot(
                animal,
                operational_date=as_of_date,
                history=history,
            )
        effective_schedule = {
            "operational_date": (
                snapshot.operational_date.isoformat()
                if snapshot.operational_date
                else None
            ),
            "milking_frequency": snapshot.milking_frequency,
            "expected_sessions": list(snapshot.expected_sessions),
            "source": snapshot.source,
            "history_id": snapshot.history_id,
            "effective_from": (
                snapshot.effective_from.isoformat()
                if snapshot.effective_from
                else None
            ),
            "effective_to": (
                snapshot.effective_to.isoformat()
                if snapshot.effective_to
                else None
            ),
            "changed_by": snapshot.changed_by,
            "reason": snapshot.reason,
        }
        return {
            "effective": effective_schedule,
            "history": [
                self._serialize_schedule(item)
                for item in history
            ],
        }

    @staticmethod
    def _serialize_schedule(record) -> dict[str, Any]:
        return {
            "id": getattr(record, "id", None),
            "animal_id": getattr(record, "animal_id", None),
            "milking_frequency": getattr(record, "milking_frequency", None),
            "effective_from": (
                getattr(record, "effective_from", None).isoformat()
                if getattr(record, "effective_from", None)
                else None
            ),
            "effective_to": (
                getattr(record, "effective_to", None).isoformat()
                if getattr(record, "effective_to", None)
                else None
            ),
            "changed_by": getattr(record, "changed_by", None),
            "reason": getattr(record, "reason", None),
        }

    def build(
        self,
        animal_id: str,
        as_of_date: date | None = None,
    ) -> dict[str, Any] | None:
        animal = self.factory.animal().get_by_animal_id(animal_id)
        if animal is None:
            return None

        settings_repository = getattr(self.factory, "app_settings", None)
        projection_date = as_of_date or (
            OperationalDateAuthority(repository_factory=self.factory).current_date()
            if callable(settings_repository)
            else utcnow().date()
        )
        all_animals = self.factory.animal().get_all()
        lineage = self._lineage_projection(animal, all_animals)

        milk = self._through_date(
            self._for_animal(self.factory.milk().get_all(), animal_id),
            as_of_date,
        )
        health = self._through_date(
            self._for_animal(self.factory.health().get_all(), animal_id),
            as_of_date,
        )
        breeding = self._through_date(
            self._for_animal(self.factory.breeding().get_all(), animal_id),
            as_of_date,
        )
        treatments = self._through_date(
            self.factory.treatment().get_by_animal(animal_id),
            as_of_date,
        )
        feed = self._through_date(
            self._for_animal(self.factory.feed().get_all(), animal_id),
            as_of_date,
        )
        finance = self._through_date(
            self._for_animal(self.factory.finance().get_all(), animal_id),
            as_of_date,
        )
        events = [
            event
            for event in self.factory.operational_events().get_all()
            if self._event_for_animal(event, animal_id)
            and (
                as_of_date is None
                or (
                    (event_date := self._record_date(event)) is not None
                    and event_date <= as_of_date
                )
            )
        ]

        history = {
            "milk": [self._serialize(item) for item in milk],
            "health": [self._serialize(item) for item in health],
            "breeding": [self._serialize(item) for item in breeding],
            "treatments": [self._serialize(item) for item in treatments],
            "feed": [self._serialize(item) for item in feed],
            "finance": [self._serialize(item) for item in finance],
            "operational_events": [self._serialize(item) for item in events],
            "lineage_descendants": [dict(item) for item in lineage["descendants"]],
        }

        timeline = []
        for domain, records in history.items():
            for record in records:
                timeline.append(
                    {
                        "domain": domain,
                        "timestamp": self._record_timestamp(record),
                        "record": record,
                    }
                )
        timeline.sort(key=lambda item: str(item["timestamp"]))

        schedule = self._schedule_projection(animal, as_of_date)
        production = self._lactation_projection(milk, breeding, projection_date)
        reproduction = self._reproductive_projection(
            animal_id,
            breeding,
            projection_date,
        )
        health_state = self._health_projection(
            animal_id,
            projection_date,
            treatments=treatments,
        )
        biological_summary = {
            "lifetime_milk_liters": production["lifetime"]["lifetime_milk_liters"],
            "lactation_count": production["lifetime"]["lactation_count"],
            "lifetime_calvings": reproduction["summary"]["lifetime_calvings"],
            "current_reproductive_status": reproduction["summary"]["current_api_status"],
            "current_pregnancy_status": reproduction["summary"]["pregnancy_status"],
            "days_in_milk": reproduction["summary"]["days_in_milk"],
            "open_health_cases": health_state["summary"]["open_case_count"],
            "active_milk_withdrawal": health_state["summary"]["active_withdrawal"],
        }

        return {
            "animal": self._animal_identity(animal),
            "date_context": {
                "mode": (
                    "CURRENT_STATE"
                    if as_of_date is None
                    else "HISTORICAL_STATE"
                ),
                "operational_date": (
                    as_of_date.isoformat()
                    if as_of_date is not None
                    else None
                ),
                "historical_state_basis": (
                    "Persisted domain records through the selected operational date plus effective-dated milking schedule authority."
                    if as_of_date is not None
                    else None
                ),
            },
            "lineage": lineage,
            "production": production,
            "reproduction": {
                "current": reproduction["summary"],
                "lifetime_events": reproduction["events"],
            },
            "health_state": health_state,
            "biological_summary": biological_summary,
            "schedule": schedule,
            "history": history,
            "timeline": timeline,
            "record_counts": {
                domain: len(records)
                for domain, records in history.items()
            },
        }
