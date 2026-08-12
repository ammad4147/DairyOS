"""Authoritative lifetime Animal Passport read model."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any


class LifetimeAnimalPassportService:
    """Project persisted animal-domain records into one read-side passport.

    The service owns projection/assembly only. Domain repositories remain the
    authoritative sources of records; no passport-specific persistence is
    introduced.
    """

    def __init__(self, repository_factory):
        self.factory = repository_factory

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

    def build(self, animal_id: str) -> dict[str, Any] | None:
        animal = self.factory.animal().get_by_animal_id(animal_id)
        if animal is None:
            return None

        milk = self._for_animal(self.factory.milk().get_all(), animal_id)
        health = self._for_animal(self.factory.health().get_all(), animal_id)
        breeding = self._for_animal(self.factory.breeding().get_all(), animal_id)
        treatments = self.factory.treatment().get_by_animal(animal_id)
        feed = self._for_animal(self.factory.feed().get_all(), animal_id)
        finance = self._for_animal(self.factory.finance().get_all(), animal_id)
        events = [
            event
            for event in self.factory.operational_events().get_all()
            if self._event_for_animal(event, animal_id)
        ]

        history = {
            "milk": [self._serialize(item) for item in milk],
            "health": [self._serialize(item) for item in health],
            "breeding": [self._serialize(item) for item in breeding],
            "treatments": [self._serialize(item) for item in treatments],
            "feed": [self._serialize(item) for item in feed],
            "finance": [self._serialize(item) for item in finance],
            "operational_events": [self._serialize(item) for item in events],
        }

        timeline = []
        for domain, records in history.items():
            for record in records:
                timeline.append({
                    "domain": domain,
                    "timestamp": self._record_timestamp(record),
                    "record": record,
                })
        timeline.sort(key=lambda item: str(item["timestamp"]))

        return {
            "animal": {
                "id": animal.id,
                "animal_id": animal.animal_id,
                "animal_type": animal.animal_type,
                "ear_tag": animal.ear_tag,
                "rfid": animal.rfid,
                "breed": animal.breed,
                "sex": animal.sex,
                "date_of_birth": animal.date_of_birth.isoformat() if animal.date_of_birth else None,
                "dam_id": getattr(animal, "dam_id", None),
                "sire_id": getattr(animal, "sire_id", None),
                "lifecycle_status": animal.lifecycle_status,
                "status": animal.status,
                "active": animal.active,
                "created_at": animal.created_at.isoformat() if animal.created_at else None,
                "updated_at": animal.updated_at.isoformat() if animal.updated_at else None,
            },
            "history": history,
            "timeline": timeline,
            "record_counts": {domain: len(records) for domain, records in history.items()},
        }
