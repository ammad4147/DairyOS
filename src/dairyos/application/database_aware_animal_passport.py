"""Compatibility wrapper for the authoritative Animal Passport service.

The application-wide Passport build pipeline is owned by
``LifetimeAnimalPassportService``. This module remains only so established
imports continue to work while cross-domain projections such as the
Knowledge Graph, persisted animal-welfare observations, and normalized
operational-event linkage are attached to the canonical Passport read model.
"""

from __future__ import annotations

from datetime import date, datetime

from dairyos.application.animal_passport import LifetimeAnimalPassportService
from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.platform.knowledge_graph.services.animal_passport_graph_service import (
    AnimalPassportGraphService,
)


class DatabaseAwareLifetimeAnimalPassportService(LifetimeAnimalPassportService):
    """Backward-compatible Passport service with database projections."""

    @staticmethod
    def _event_matches_animal(event, animal_id: str) -> bool:
        target = str(animal_id)
        for key in ("animal_id", "entity_id"):
            value = getattr(event, key, None)
            if value is not None and str(value) == target:
                return True

        payload = getattr(event, "payload", None)
        if isinstance(payload, dict):
            for key in ("animal_id", "entity_id", "animalId", "entityId"):
                value = payload.get(key)
                if value is not None and str(value) == target:
                    return True

        description = str(getattr(event, "description", ""))
        return (
            f"entity_id={target}" in description
            or f"animal_id={target}" in description
        )

    @staticmethod
    def _event_date(event):
        for key in ("event_date", "timestamp", "created_at", "updated_at"):
            value = getattr(event, key, None)
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, date):
                return value
            if value:
                try:
                    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
                except ValueError:
                    continue
        return None

    def _operational_event_projection(self, animal_id: str, as_of_date: date | None):
        events = []
        for event in self.factory.operational_events().get_all():
            if not self._event_matches_animal(event, animal_id):
                continue
            event_date = self._event_date(event)
            if as_of_date is not None and (
                event_date is None or event_date > as_of_date
            ):
                continue
            events.append(event)
        return events

    def _welfare_projection(self, animal_id: str, as_of_date: date | None):
        session = getattr(self.factory, "session", None)
        if session is None:
            return {
                "data_status": "UNAVAILABLE",
                "observation_count": 0,
                "observations": [],
            }

        model = (
            session.query(OperationalStateModel)
            .filter(OperationalStateModel.farm_id == "DEFAULT")
            .first()
        )
        raw = list((model.state_payload or {}).get("animal_welfare_observations", [])) if model else []
        observations = []
        for item in raw:
            if str(item.get("animal_id", "")) != str(animal_id):
                continue
            observed_at = item.get("observed_at")
            try:
                observed_date = datetime.fromisoformat(
                    str(observed_at).replace("Z", "+00:00")
                ).date()
            except (TypeError, ValueError):
                observed_date = None
            if as_of_date is not None and (
                observed_date is None or observed_date > as_of_date
            ):
                continue
            observations.append(dict(item))

        observations.sort(key=lambda item: str(item.get("observed_at", "")))
        return {
            "data_status": "LIVE_PERSISTED_DATA" if observations else "NO_DATA",
            "observation_count": len(observations),
            "latest": observations[-1] if observations else None,
            "observations": observations,
        }

    def build(self, animal_id: str, as_of_date: date | None = None):
        passport = super().build(animal_id, as_of_date=as_of_date)
        if passport is None:
            return None

        operational_events = self._operational_event_projection(animal_id, as_of_date)
        passport["history"]["operational_events"] = [
            self._serialize(item) for item in operational_events
        ]
        passport["record_counts"]["operational_events"] = len(operational_events)
        passport["timeline"] = [
            {
                "domain": domain,
                "timestamp": self._record_timestamp(record),
                "record": record,
            }
            for domain, records in passport["history"].items()
            for record in records
        ]
        passport["timeline"].sort(key=lambda item: str(item["timestamp"]))

        welfare = self._welfare_projection(animal_id, as_of_date)
        health_state = passport.setdefault("health_state", {})
        health_state["welfare"] = welfare
        passport["history"]["welfare"] = [dict(item) for item in welfare["observations"]]
        passport["record_counts"]["welfare"] = len(passport["history"]["welfare"])
        passport["timeline"].extend(
            {
                "domain": "welfare",
                "timestamp": item.get("observed_at", ""),
                "record": dict(item),
            }
            for item in passport["history"]["welfare"]
        )
        passport["timeline"].sort(key=lambda item: str(item["timestamp"]))
        passport["knowledge_graph"] = AnimalPassportGraphService().build(
            animal_id,
            passport["lineage"],
            passport["history"],
        )
        return passport
