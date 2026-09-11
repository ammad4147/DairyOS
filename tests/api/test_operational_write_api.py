import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from dairyos.app import container
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.milking_session_record import MilkingSessionRecord
from dairyos.data.models.operational_write import OperationalProjectionOutbox
from dairyos.data.models.treatment_record import TreatmentRecord
from dairyos.data.repositories.milking_session_record_repository import MilkingSessionRecordRepository


def _milk(animal, **extra):
    return {"animal_id": animal, "morning_yield": 11, "operator": "tester", **extra}


def _rows(model):
    with Session(container.repository_factory.session.get_bind()) as session:
        return session.query(model).count()


def test_api_projection_failure_keeps_one_milk_and_one_journal_after_retry(client, registered_animal, monkeypatch):
    request = _milk(registered_animal, request_id="milk-retry")
    original = container.input_ingestion_service.repository._persist
    monkeypatch.setattr(container.input_ingestion_service.repository, "_persist", lambda: (_ for _ in ()).throw(PermissionError("denied")))
    response = client.post("/farm/milk", json=request)
    assert response.status_code == 200, response.text
    assert response.json()["persistence_status"] == "ACCEPTED"
    assert response.json()["projection_status"] == "DEGRADED"
    assert _rows(MilkProduction) == 1
    monkeypatch.setattr(container.input_ingestion_service.repository, "_persist", original)
    retry = client.post("/farm/milk", json=request)
    assert retry.status_code == 200, retry.text
    assert retry.json()["projection_status"] == "DELIVERED"
    assert _rows(MilkProduction) == 1
    state = container.operational_state_service.get_state()
    assert state.milk_production_summary["total_litres_today"] == 11
    again = client.post("/farm/milk", json=request)
    assert again.status_code == 200
    assert state.milk_production_summary["total_litres_today"] == 11
    changed = client.post("/farm/milk", json={**request, "morning_yield": 15})
    assert changed.status_code == 409


def test_late_session_failure_rolls_back_milk_journal_and_outbox(client, registered_animal, monkeypatch):
    before_journal = _rows(EventJournalModel)
    before_outbox = _rows(OperationalProjectionOutbox)

    def fail(*args, **kwargs):
        raise RuntimeError("session settlement failed")

    monkeypatch.setattr(MilkingSessionRecordRepository, "settle", fail)
    with pytest.raises(RuntimeError, match="settlement failed"):
        client.post("/farm/milk", json=_milk(registered_animal, milking_session="MORNING"))
    assert _rows(MilkProduction) == 0
    assert _rows(MilkingSessionRecord) == 0
    # The registered-animal fixture is itself an operational write and leaves
    # its delivered receipt behind. The failed Milk command must not add a
    # second receipt or journal entry.
    assert _rows(OperationalProjectionOutbox) == before_outbox
    assert _rows(EventJournalModel) == before_journal


def test_treatment_projection_failure_does_not_hide_withdrawal_from_next_milk(client, registered_animal, monkeypatch):
    original = container.input_ingestion_service.repository._persist
    monkeypatch.setattr(container.input_ingestion_service.repository, "_persist", lambda: (_ for _ in ()).throw(PermissionError("denied")))
    treatment = client.post("/farm/treatments", json={
        "animal_id": registered_animal, "medicine": "manual", "milk_withdrawal_days": 4,
        "operator": "tester", "request_id": "treatment-retry",
    })
    assert treatment.status_code == 200, treatment.text
    assert treatment.json()["projection_status"] == "DEGRADED"
    milk = client.post("/farm/milk", json=_milk(registered_animal))
    assert milk.status_code == 200, milk.text
    assert milk.json()["withdrawal_warning"] is True
    assert milk.json()["withdrawal_wastage_litres"] == 11
    monkeypatch.setattr(container.input_ingestion_service.repository, "_persist", original)
    assert client.post("/farm/operational-projections/retry").json()["projection_status"] == "DELIVERED"
    assert _rows(TreatmentRecord) == 1


def test_delivery_ack_failure_does_not_double_project_milk(client, registered_animal):
    def fail(*args):
        raise RuntimeError("delivery acknowledgement failure")

    event.listen(OperationalProjectionOutbox, "before_update", fail)
    try:
        response = client.post("/farm/milk", json=_milk(registered_animal, request_id="ack-retry"))
        assert response.status_code == 200, response.text
        assert response.json()["projection_status"] == "DEGRADED"
    finally:
        event.remove(OperationalProjectionOutbox, "before_update", fail)
    assert container.operational_state_service.get_state().milk_production_summary["total_litres_today"] == 11
    assert client.post("/farm/operational-projections/retry").json()["projection_status"] == "DELIVERED"
    assert container.operational_state_service.get_state().milk_production_summary["total_litres_today"] == 11


def test_pending_delivery_recovers_through_runtime_restart(client, registered_animal, monkeypatch):
    original = container.input_ingestion_service.event_publisher
    monkeypatch.setattr(container.input_ingestion_service, "event_publisher", lambda _: (_ for _ in ()).throw(RuntimeError("offline")))
    response = client.post("/farm/milk", json=_milk(registered_animal))
    assert response.json()["projection_status"] == "DEGRADED"
    monkeypatch.setattr(container.input_ingestion_service, "event_publisher", original)
    container.stop()
    container.start()
    assert container.projection_delivery_status["projection_status"] == "DELIVERED"
    assert container.operational_state_service.get_state().milk_production_summary["total_litres_today"] == 11
    container.stop()
    container.start()
    assert container.operational_state_service.get_state().milk_production_summary["total_litres_today"] == 11
