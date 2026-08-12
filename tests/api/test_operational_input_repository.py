from datetime import datetime, timezone

from dairyos.domain.events.operational_input_received import OperationalInputReceived
from dairyos.farm.inputs.repository.operational_input_repository import (
    OperationalInputRepository,
)


def test_operational_input_repository_survives_repository_restart(tmp_path):
    path = tmp_path / "operational_inputs.json"
    timestamp = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
    event = OperationalInputReceived(
        input_type="milk_production",
        payload={
            "animal_id": "TEST-COW-001",
            "morning_yield": 8.0,
        },
        source="API",
        actor="Operator",
        event_id="H07-RESTART-001",
        timestamp=timestamp,
    )

    first = OperationalInputRepository(storage_path=path)
    first.save(event)

    second = OperationalInputRepository(storage_path=path)
    records = second.list_all()

    assert len(records) == 1
    assert records[0].event_id == "H07-RESTART-001"
    assert records[0].input_type == "milk_production"
    assert records[0].payload["animal_id"] == "TEST-COW-001"
    assert records[0].timestamp == timestamp


def test_operational_input_repository_deduplicates_event_identity(tmp_path):
    path = tmp_path / "operational_inputs.json"
    event = OperationalInputReceived(
        input_type="health_observation",
        payload={"animal_id": "TEST-COW-002"},
        source="API",
        actor="Vet",
        event_id="H07-DEDUPE-001",
    )

    repository = OperationalInputRepository(storage_path=path)
    repository.save(event)
    repository.save(event)

    assert len(repository.list_all()) == 1
    assert len(repository.find_by_type("health_observation")) == 1
