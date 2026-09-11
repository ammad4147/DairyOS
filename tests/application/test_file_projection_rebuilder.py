from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from dairyos.application.file_projection_rebuilder import FileProjectionRebuilder
from dairyos.domain.events.operational_input_received import OperationalInputReceived
from dairyos.farm.herd.models.animal_operational_state import AnimalOperationalState
from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)
from dairyos.farm.herd.services.animal_event_projection import AnimalEventProjection
from dairyos.farm.inputs.repository.operational_input_repository import (
    OperationalInputRepository,
)


@dataclass
class JournalEntry:
    event_type: str
    payload: dict
    event_id: str
    timestamp: datetime


class Journal:
    def __init__(self, entries):
        self.entries = entries

    def all_entries(self):
        return list(self.entries)


def _rebuilder(tmp_path, journal):
    input_path = tmp_path / "operational_inputs.json"
    state_path = tmp_path / "animal_operational_states.json"
    inputs = OperationalInputRepository(input_path)
    states = AnimalOperationalStateRepository(state_path)
    return (
        FileProjectionRebuilder(
            event_journal=journal,
            operational_input_repository=inputs,
            animal_operational_state_repository=states,
            animal_event_projection=AnimalEventProjection(repository=states),
        ),
        input_path,
        state_path,
        inputs,
        states,
    )


def test_rebuild_promotes_complete_empty_projections(tmp_path):
    rebuilder, input_path, state_path, _inputs, _states = _rebuilder(
        tmp_path,
        Journal([]),
    )

    rebuilder.rebuild()

    assert input_path.read_text(encoding="utf-8").strip() == "[]"
    assert state_path.read_text(encoding="utf-8").strip() == "[]"


def test_rebuild_failure_leaves_last_known_good_projections(tmp_path):
    rebuilder, input_path, state_path, inputs, states = _rebuilder(
        tmp_path,
        None,
    )
    timestamp = datetime.now(UTC)
    inputs.save(
        OperationalInputReceived(
            input_type="equipment",
            payload={"equipment_id": "OLD"},
            source="test",
            actor="test",
            event_id="old-input",
            timestamp=timestamp,
        )
    )
    states.save(AnimalOperationalState(animal_id="OLD"))
    old_input = input_path.read_bytes()
    old_state = state_path.read_bytes()

    class FailingJournal:
        def all_entries(self):
            def entries():
                yield JournalEntry(
                    event_type="AnimalCreated",
                    payload={"animal_id": "NEW", "animal_type": "CALF"},
                    event_id="new-animal",
                    timestamp=timestamp,
                )
                raise RuntimeError("journal replay failed")

            return entries()

    rebuilder.event_journal = FailingJournal()

    with pytest.raises(RuntimeError, match="journal replay failed"):
        rebuilder.rebuild()

    assert input_path.read_bytes() == old_input
    assert state_path.read_bytes() == old_state
