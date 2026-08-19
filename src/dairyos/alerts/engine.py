"""Compatibility adapter for legacy event-driven alerts.

Phase 3 governance rule: legacy alerts must enter the persisted
OperationalFinding lifecycle rather than remaining log-only warnings.
"""

import logging

from dairyos.domain.events import Event
from dairyos.farm.findings.services.operational_finding_service import (
    OperationalFindingService,
)

log = logging.getLogger(__name__)


class AlertEngine:
    """Translate legacy alert events into governed operational findings."""

    def __init__(self, container=None, finding_service=None):
        self.container = container
        self.finding_service = finding_service

    def _get_finding_service(self):
        if self.finding_service is not None:
            return self.finding_service

        from dairyos.data.repositories.repository_factory import RepositoryFactory

        factory = RepositoryFactory.create()
        try:
            return OperationalFindingService(factory.operational_findings()), factory
        except Exception:
            factory.close()
            raise

    def handle_event(self, event: Event):
        if event.name == "MilkRecorded":
            qty = event.payload.get("quantity", 0)
            if qty < 1.0:
                animal_id = event.payload.get("animal_id")
                session = event.payload.get("milking_session")
                detail = f"Milk quantity {qty} L is below the alert threshold."
                if animal_id:
                    detail += f" Animal: {animal_id}."

                dedupe_key = (
                    f"LOW_MILK:{animal_id or '__farm__'}:{session or '__unknown__'}"
                )

                owned_factory = None
                try:
                    service = self._get_finding_service()
                    if isinstance(service, tuple):
                        service, owned_factory = service

                    service.raise_or_update(
                        source_module="MILK",
                        severity="HIGH",
                        title="Low milk yield recorded",
                        detail=detail,
                        subject_type="animal" if animal_id else "farm",
                        subject_id=str(animal_id) if animal_id else None,
                        route="milk",
                        dedupe_key=dedupe_key,
                    )
                except Exception:
                    log.exception("Failed to persist legacy milk alert as an operational finding.")
                finally:
                    if owned_factory is not None:
                        owned_factory.close()

        if self.container is not None and getattr(self.container, "dashboard", None) is not None:
            self.container.dashboard.rebuild()
