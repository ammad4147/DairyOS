from sqlalchemy.orm import Session

from dairyos.api import breeding_biology
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.database.session import engine
from dairyos.data.models.breeding_propagation_outbox import BreedingPropagationOutbox


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
    original = breeding_biology._deliver_breeding_propagation

    def fail_delivery(container, propagation_id):
        bind = container.repository_factory.session.get_bind()
        with Session(bind=bind) as session:
            row = session.query(BreedingPropagationOutbox).filter_by(
                propagation_id=propagation_id
            ).one()
            row.attempts += 1
            row.status = "PENDING"
            row.last_error = "injected projection failure"
            session.commit()
            session.refresh(row)
            return row

    monkeypatch.setattr(
        breeding_biology,
        "_deliver_breeding_propagation",
        fail_delivery,
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
        assert row.record_id == payload["record_id"]

    monkeypatch.setattr(
        breeding_biology,
        "_deliver_breeding_propagation",
        original,
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
