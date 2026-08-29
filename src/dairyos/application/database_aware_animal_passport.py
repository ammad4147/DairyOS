"""Compatibility wrapper for the authoritative Animal Passport service.

The application-wide Passport build pipeline is owned by
``LifetimeAnimalPassportService``.  This module remains only so established
imports continue to work while the Knowledge Graph projection is attached to
the canonical Passport read model.
"""

from __future__ import annotations

from datetime import date

from dairyos.application.animal_passport import LifetimeAnimalPassportService
from dairyos.platform.knowledge_graph.services.animal_passport_graph_service import (
    AnimalPassportGraphService,
)


class DatabaseAwareLifetimeAnimalPassportService(LifetimeAnimalPassportService):
    """Backward-compatible Passport service with graph projection."""

    def build(self, animal_id: str, as_of_date: date | None = None):
        passport = super().build(animal_id, as_of_date=as_of_date)
        if passport is None:
            return None
        passport["knowledge_graph"] = AnimalPassportGraphService().build(
            animal_id,
            passport["lineage"],
            passport["history"],
        )
        return passport
