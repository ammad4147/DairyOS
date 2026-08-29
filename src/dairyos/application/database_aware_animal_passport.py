"""Compatibility wrapper for the authoritative Animal Passport service.

The application-wide Passport build pipeline is owned by
``LifetimeAnimalPassportService``. This module remains only so established
imports continue to work while cross-domain projections such as the
Knowledge Graph and persisted animal-welfare observations are attached to
the canonical Passport read model.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from dairyos.application.animal_passport import LifetimeAnimalPassportService
from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.platform.knowledge_graph.services.animal_passport_graph_service import (
    AnimalPassportGraphService,
)


class DatabaseAwareLifetimeAnimalPassportService(LifetimeAnimalPassportService):
    """Backward-compatible Passport service with database projections."""

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

        welfare = self._welfare_projection(animal_id, as_of_date)
        health_state = passport.setdefault("health_state", {})
        health_state["welfare"] = welfare
        passport["knowledge_graph"] = AnimalPassportGraphService().build(
            animal_id,
            passport["lineage"],
            passport["history"],
        )
        return passport
