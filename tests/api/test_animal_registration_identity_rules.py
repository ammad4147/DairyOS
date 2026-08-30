from fastapi.testclient import TestClient

from dairyos.app import app, container
from dairyos.data.database.session import SessionLocal
from dairyos.data.models.animal import Animal
from dairyos.data.models.animal_milking_schedule_history import AnimalMilkingScheduleHistory
from dairyos.runtime.persistent_event_journal import PersistentEventJournal


client = TestClient(app)


def _reset_animals():
    journal = PersistentEventJournal()
    journal.clear()
    container.event_journal = journal
    session = SessionLocal()
    try:
        session.query(AnimalMilkingScheduleHistory).delete(synchronize_session=False)
        session.query(Animal).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


def setup_function():
    _reset_animals()


def test_registration_generates_permanent_id_and_preserves_old_identity_and_acquisition_date():
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "animal_category": "Milking",
            "legacy_animal_id": "OLD-4711",
            "ear_tag": "EAR-99",
            "date_of_acquisition": "2026-08-30",
            "breed": "HF",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["system_generated_animal_id"] is True
    assert body["animal_id"].startswith("TD-")
    assert body["animal_id"] != "OLD-4711"
    assert body["legacy_animal_id"] == "OLD-4711"
    assert body["date_of_acquisition"] == "2026-08-30"
    assert body["milking_frequency"] == "TWICE_DAILY"


def test_registration_rejects_milking_frequency_for_non_milking_category():
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "animal_category": "Heifer",
            "milking_frequency": "TWICE_DAILY",
        },
    )

    assert response.status_code == 422
    assert "only applicable" in response.json()["detail"]


def test_registration_allows_no_milking_frequency_for_non_milking_category():
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "animal_category": "Heifer",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["milking_frequency"] is None
    assert body["is_currently_milking"] is False


def test_registration_rejects_duplicate_old_animal_id():
    first = client.post(
        "/farm/animals",
        json={"animal_type": "CATTLE", "animal_category": "Heifer", "legacy_animal_id": "OLD-100"},
    )
    assert first.status_code == 200

    second = client.post(
        "/farm/animals",
        json={"animal_type": "CATTLE", "animal_category": "Bull", "legacy_animal_id": "OLD-100"},
    )
    assert second.status_code == 409
