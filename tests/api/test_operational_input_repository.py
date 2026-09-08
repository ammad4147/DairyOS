from datetime import UTC, datetime

import pytest

from dairyos.domain.events.operational_input_received import OperationalInputReceived
from dairyos.farm.inputs.repository.operational_input_repository import (
    OperationalInputRepository,
)


def test_operational_input_repository_survives_repository_restart(tmp_path):
    path = tmp_path / "operational_inputs.json"
    timestamp = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
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


def test_operational_input_api_record_is_visible_after_repository_reopen(
    client,
    registered_animal,
):
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "operator": "Milking Operator",
        },
    )
    assert response.status_code == 200, response.text

    reopened = OperationalInputRepository()
    records = reopened.find_by_type("milk_production")

    assert records
    assert records[-1].payload["animal_id"] == registered_animal
    assert records[-1].payload["morning_yield"] == 8.0


def test_failed_materialization_can_be_retried_without_false_deduplication(
    tmp_path, monkeypatch
):
    repository = OperationalInputRepository(tmp_path / "inputs.json")
    event = OperationalInputReceived(
        "equipment", {"equipment_id": "TEST"}, "API", "test"
    )
    persist = repository._persist

    def fail():
        raise PermissionError("injected atomic replacement failure")

    monkeypatch.setattr(repository, "_persist", fail)
    with pytest.raises(PermissionError):
        repository.save(event)
    assert repository.list_all() == []
    monkeypatch.setattr(repository, "_persist", persist)
    repository.save(event)
    repository.save(event)
    reopened = OperationalInputRepository(repository.storage_path)
    assert [record.event_id for record in reopened.list_all()] == [event.event_id]


def test_failed_clear_keeps_in_memory_and_durable_state_consistent(
    tmp_path, monkeypatch
):
    repository = OperationalInputRepository(tmp_path / "inputs.json")
    event = OperationalInputReceived(
        "equipment", {"equipment_id": "TEST"}, "API", "test"
    )
    repository.save(event)

    def fail():
        raise OSError("injected write failure")

    monkeypatch.setattr(repository, "_persist", fail)
    with pytest.raises(OSError):
        repository.clear()
    assert repository.list_all() == [event]
    assert len(OperationalInputRepository(repository.storage_path).list_all()) == 1
