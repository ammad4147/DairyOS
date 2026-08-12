from fastapi.testclient import TestClient
import pytest

from dairyos.app import app, container
from dairyos.runtime.persistent_event_journal import PersistentEventJournal
from dairyos.farm.operations.state.farm_operational_state_service import FarmOperationalStateService
from dairyos.data.database.session import SessionLocal
from dairyos.data.models.animal import Animal
from dairyos.data.models.animal_milking_schedule_history import AnimalMilkingScheduleHistory


@pytest.fixture(autouse=True)
def reset_runtime_state():
    """Isolate persistent animal state before every API test."""
    journal = PersistentEventJournal()
    journal.clear()
    container.event_journal = journal

    session = SessionLocal()
    try:
        session.query(AnimalMilkingScheduleHistory).delete(synchronize_session=False)
        session.query(Animal).delete(synchronize_session=False)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    container.farm_operational_state_service = FarmOperationalStateService()
    container.stop()
    container.operations = None
    container.dashboard = None


client = TestClient(app)


def create_animal(**overrides):
    payload = {
        "animal_type": "COW",
        "breed": "Sahiwal",
        "lifecycle_status": "LACTATING",
    }
    payload.update(overrides)
    return client.post("/farm/animals", json=payload)


def test_create_animal_generates_permanent_id():
    response = create_animal(is_currently_milking=True, milking_frequency="THRICE_DAILY")

    assert response.status_code == 200
    body = response.json()
    assert body["system_generated_animal_id"] is True
    assert body["animal_id"].startswith("AN-")
    assert len(body["animal_id"]) == 35
    assert body["lifecycle_status"] == "LACTATING"
    assert body["is_currently_milking"] is True
    assert body["milking_frequency"] == "THRICE_DAILY"
    assert body["active"] is True


def test_create_animal_rejects_client_supplied_permanent_id():
    response = client.post(
        "/farm/animals",
        json={
            "animal_id": "OPERATOR-CHOSEN-ID",
            "animal_type": "COW",
            "lifecycle_status": "LACTATING",
        },
    )

    assert response.status_code == 400
    assert "system-generated" in response.json()["detail"]


def test_create_animal_ids_are_unique_and_persistent():
    first = create_animal()
    second = create_animal()

    assert first.status_code == 200
    assert second.status_code == 200

    first_id = first.json()["animal_id"]
    second_id = second.json()["animal_id"]
    assert first_id != second_id

    response = client.get(f"/farm/animals/{first_id}")
    assert response.status_code == 200
    assert response.json()["animal_id"] == first_id


def test_create_animal_invalid_lifecycle_status_rejected():
    response = create_animal(lifecycle_status="NOT_A_REAL_STATUS")
    assert response.status_code == 422


def test_get_animal():
    created = create_animal()
    animal_id = created.json()["animal_id"]

    response = client.get(f"/farm/animals/{animal_id}")

    assert response.status_code == 200
    assert response.json()["animal_id"] == animal_id


def test_get_nonexistent_animal_404():
    response = client.get("/farm/animals/DOES-NOT-EXIST")
    assert response.status_code == 404


def test_list_animals():
    response = client.get("/farm/animals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_currently_milking_animals():
    created = create_animal(
        is_currently_milking=True,
        milking_frequency="TWICE_DAILY",
    )
    animal_id = created.json()["animal_id"]

    response = client.get("/farm/animals?currently_milking=true")

    assert response.status_code == 200
    animal_ids = [animal["animal_id"] for animal in response.json()]
    assert animal_id in animal_ids


def test_change_milking_frequency_confirmed_flow():
    """Milking frequency is per-animal and retains complete history."""
    created = create_animal(milking_frequency="THRICE_DAILY")
    animal_id = created.json()["animal_id"]

    response = client.post(
        f"/farm/animals/{animal_id}/milking-frequency",
        json={
            "milking_frequency": "TWICE_DAILY",
            "changed_by": "test-manager",
            "reason": "End of lactation cycle",
        },
    )

    assert response.status_code == 200
    assert response.json()["milking_frequency"] == "TWICE_DAILY"

    history_response = client.get(
        f"/farm/animals/{animal_id}/milking-frequency/history"
    )

    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 2
    assert history[0]["milking_frequency"] == "TWICE_DAILY"
    assert history[0]["effective_to"] is None
    assert history[0]["reason"] == "End of lactation cycle"
    assert history[1]["milking_frequency"] == "THRICE_DAILY"
    assert history[1]["effective_to"] is not None


def test_change_milking_frequency_invalid_value_rejected():
    created = create_animal()
    animal_id = created.json()["animal_id"]

    response = client.post(
        f"/farm/animals/{animal_id}/milking-frequency",
        json={"milking_frequency": "FOUR_TIMES_DAILY"},
    )

    assert response.status_code == 422
