"""Canonical reconstruction of event-owned file projections."""

from __future__ import annotations

from dairyos.domain.events import Event
from dairyos.domain.events.operational_input_received import OperationalInputReceived


class FileProjectionRebuilder:
    """Rebuild JSON projections from the one durable event-journal authority."""

    def __init__(
        self,
        *,
        event_journal,
        operational_input_repository,
        animal_operational_state_repository,
        animal_event_projection,
    ):
        self.event_journal = event_journal
        self.operational_input_repository = operational_input_repository
        self.animal_operational_state_repository = animal_operational_state_repository
        self.animal_event_projection = animal_event_projection

    def rebuild(self) -> None:
        self.operational_input_repository.clear()
        self.animal_operational_state_repository.clear()

        for entry in self.event_journal.all_entries():
            event = Event(
                name=entry.event_type,
                payload=dict(entry.payload),
                timestamp=entry.timestamp.isoformat(),
            )
            if entry.event_type == "OperationalInputReceived":
                payload = dict(entry.payload)
                self.operational_input_repository.save(
                    OperationalInputReceived(
                        input_type=str(payload["input_type"]),
                        payload=payload,
                        source=str(payload.get("source", "")),
                        actor=str(payload.get("actor", "")),
                        event_id=entry.event_id,
                        timestamp=entry.timestamp,
                    )
                )
            self.animal_event_projection.apply(event)
