import pytest
from sqlalchemy.orm import Session

from dairyos.app import container
from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.database.session import engine
from dairyos.data.models.breeding_propagation_outbox import BreedingPropagationOutbox
from dairyos.farm.operations.repositories.adapters.database_breeding_repository import (
    DatabaseBreedingRepository,
)


def _post(client, animal_id, event_type, result):
    return client.post(
        "/farm/breeding",
        json={
            "animal_id": animal_id,
            "event_type": event_type,
            "result": result,
            "technician": "Dr Vet",
            "operator": "Dr Vet",
        },
    )


def test_projection_failure_keeps_durable_pending_outbox(
    client,
    registered_animal,
    monkeypatch,
):
    original_publisher = container.input_ingestion_service.event_publisher

    def fail_publish(event):
        raise RuntimeError("injected operational projection failure")

    monkeypatch.setattr(
        container.input_ingestion_service,
        "event_publisher",
        fail_publish,
    )
    response = _post(client, registered_animal, "insemination", "COMPLETED")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["propagation_status"] == "DEGRADED"
    propagation_id = payload["propagation"]["propagation_id"]

    with Session(engine) as session:
        row = session.query(BreedingPropagationOutbox).filter_by(
            propagation_id=propagation_id
        ).one()
        assert row.status == "PENDING"
        assert "injected operational projection failure" in row.last_error
        assert row.record_id == payload["record_id"]

    monkeypatch.setattr(
        container.input_ingestion_service,
        "event_publisher",
        original_publisher,
    )
    retry = client.post(
        f"/farm/breeding/propagation/{propagation_id}/retry"
    )
    assert retry.status_code == 200, retry.text
    assert retry.json()["status"] == "DELIVERED"


def test_retry_is_idempotent_in_operational_event_journal(
    client,
    registered_animal,
):
    response = _post(client, registered_animal, "insemination", "COMPLETED")
    assert response.status_code == 200, response.text
    propagation_id = response.json()["propagation"]["propagation_id"]

    first_retry = client.post(
        f"/farm/breeding/propagation/{propagation_id}/retry"
    )
    second_retry = client.post(
        f"/farm/breeding/propagation/{propagation_id}/retry"
    )
    assert first_retry.status_code == 200
    assert second_retry.status_code == 200

    with Session(engine) as session:
        assert (
            session.query(EventJournalModel)
            .filter(EventJournalModel.event_id == propagation_id)
            .count()
            == 1
        )


def test_calving_and_outbox_are_committed_as_one_postgresql_action(
    client,
    registered_animal,
):
    assert _post(client, registered_animal, "insemination", "COMPLETED").status_code == 200
    assert _post(client, registered_animal, "pregnancy_confirmed", "POSITIVE").status_code == 200

    calving = _post(client, registered_animal, "calving", "COMPLETED")
    assert calving.status_code == 200, calving.text
    payload = calving.json()
    assert payload["propagation"]["record_id"] == payload["record_id"]
    assert payload["propagation_status"] in {"DELIVERED", "DEGRADED"}

    status = client.get("/farm/breeding/propagation")
    assert status.status_code == 200, status.text
    assert any(
        row["record_id"] == payload["record_id"]
        for row in status.json()
    )


def test_postgresql_failure_rolls_back_breeding_and_outbox_together(
    client,
    registered_animal,
    monkeypatch,
):
    original_save = DatabaseBreedingRepository.save

    def fail_after_flush(self, record, *, commit=True):
        original_save(self, record, commit=False)
        raise RuntimeError("injected PostgreSQL unit-of-work failure")

    monkeypatch.setattr(DatabaseBreedingRepository, "save", fail_after_flush)

    with pytest.raises(RuntimeError, match="injected PostgreSQL unit-of-work failure"):
        _post(client, registered_animal, "insemination", "COMPLETED")

    with Session(engine) as session:
        assert (
            session.query(BreedingRecordModel)
            .filter(BreedingRecordModel.animal_id == registered_animal)
            .count()
            == 0
        )
        assert (
            session.query(BreedingPropagationOutbox)
            .filter(BreedingPropagationOutbox.animal_id == registered_animal)
            .count()
            == 0
        )
