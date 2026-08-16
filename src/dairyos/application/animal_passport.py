"""Authoritative Animal Passport read model."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from dairyos.farm.herd.services.animal_milking_schedule_service import (
    AnimalMilkingScheduleService,
)


class LifetimeAnimalPassportService:
    """Project persisted animal-domain records into one read-side passport.

    The service owns projection/assembly only. Domain repositories remain
    authoritative; no passport-specific persistence is introduced.

    When ``as_of_date`` is supplied, dated history is projected up to that
    operational date and the effective milking schedule is resolved through
    ``AnimalMilkingScheduleService``.
    """

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
    def _for_animal(records, animal_id: str):
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
                    return datetime.fromisoformat(
                        str(value)
                    ).date()
                except ValueError:
                    continue

        return None

    @classmethod
    def _through_date(
        cls,
        records,
        as_of_date: date | None,
    ):
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
    def _event_for_animal(event, animal_id: str) -> bool:
        description = str(getattr(event, "description", ""))

        return (
            f"entity_id={animal_id}" in description
            or f"animal_id={animal_id}" in description
        )

    @staticmethod
    def _record_timestamp(record: dict[str, Any]):
        for key in (
            "production_date",
            "observation_date",
            "observed_at",
            "feeding_date",
            "transaction_date",
            "treated_at",
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
    def _serialize_schedule(record) -> dict[str, Any]:
        return {
            "id": getattr(record, "id", None),
            "animal_id": getattr(record, "animal_id", None),
            "milking_frequency": getattr(
                record,
                "milking_frequency",
                None,
            ),
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
            "changed_by": getattr(
                record,
                "changed_by",
                None,
            ),
            "reason": getattr(
                record,
                "reason",
                None,
            ),
        }

    def _schedule_projection(
        self,
        animal,
        as_of_date: date | None,
    ) -> dict[str, Any]:
        history = list(
            self.factory.animal().get_milking_frequency_history(
                animal.animal_id
            )
        )

        if as_of_date is None:
            snapshot = self.schedule_service.get_schedule_snapshot(
                animal
            )
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
            "expected_sessions": list(
                snapshot.expected_sessions
            ),
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

        schedule_history = [
            self._serialize_schedule(item)
            for item in history
        ]

        return {
            "effective": effective_schedule,
            "history": schedule_history,
        }

    def build(
        self,
        animal_id: str,
        as_of_date: date | None = None,
    ) -> dict[str, Any] | None:
        animal = self.factory.animal().get_by_animal_id(
            animal_id
        )

        if animal is None:
            return None

        milk = self._through_date(
            self._for_animal(
                self.factory.milk().get_all(),
                animal_id,
            ),
            as_of_date,
        )

        health = self._through_date(
            self._for_animal(
                self.factory.health().get_all(),
                animal_id,
            ),
            as_of_date,
        )

        breeding = self._through_date(
            self._for_animal(
                self.factory.breeding().get_all(),
                animal_id,
            ),
            as_of_date,
        )

        treatments = self._through_date(
            self.factory.treatment().get_by_animal(
                animal_id
            ),
            as_of_date,
        )

        feed = self._through_date(
            self._for_animal(
                self.factory.feed().get_all(),
                animal_id,
            ),
            as_of_date,
        )

        finance = self._through_date(
            self._for_animal(
                self.factory.finance().get_all(),
                animal_id,
            ),
            as_of_date,
        )

        events = [
            event
            for event in self.factory.operational_events().get_all()
            if self._event_for_animal(
                event,
                animal_id,
            )
            and (
                as_of_date is None
                or (
                    event_date := self._record_date(event)
                ) is not None
                and event_date <= as_of_date
            )
        ]

        history = {
            "milk": [
                self._serialize(item)
                for item in milk
            ],
            "health": [
                self._serialize(item)
                for item in health
            ],
            "breeding": [
                self._serialize(item)
                for item in breeding
            ],
            "treatments": [
                self._serialize(item)
                for item in treatments
            ],
            "feed": [
                self._serialize(item)
                for item in feed
            ],
            "finance": [
                self._serialize(item)
                for item in finance
            ],
            "operational_events": [
                self._serialize(item)
                for item in events
            ],
        }

        timeline = []

        for domain, records in history.items():
            for record in records:
                timeline.append(
                    {
                        "domain": domain,
                        "timestamp": self._record_timestamp(
                            record
                        ),
                        "record": record,
                    }
                )

        timeline.sort(
            key=lambda item: str(
                item["timestamp"]
            )
        )

        schedule = self._schedule_projection(
            animal,
            as_of_date,
        )

        return {
            "animal": {
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
                "dam_id": getattr(
                    animal,
                    "dam_id",
                    None,
                ),
                "sire_id": getattr(
                    animal,
                    "sire_id",
                    None,
                ),
                "lifecycle_status": animal.lifecycle_status,
                "status": animal.status,
                "active": animal.active,
                "created_at": (
                    animal.created_at.isoformat()
                    if animal.created_at
                    else None
                ),
                "updated_at": (
                    animal.updated_at.isoformat()
                    if animal.updated_at
                    else None
                ),
            },
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
                    "Persisted domain records through the selected "
                    "operational date plus effective-dated milking "
                    "schedule authority."
                    if as_of_date is not None
                    else None
                ),
            },
            "schedule": schedule,
            "history": history,
            "timeline": timeline,
            "record_counts": {
                domain: len(records)
                for domain, records in history.items()
            },
        }
