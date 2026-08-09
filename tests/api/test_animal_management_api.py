from fastapi.testclient import TestClient
import pytest

from dairyos.app import app, container
from dairyos.runtime.persistent_event_journal import (
    PersistentEventJournal,
)
from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.data.database.session import SessionLocal
from dairyos.data.models.animal import Animal
from dairyos.data.models.animal_milking_schedule_history import (
    AnimalMilkingScheduleHistory,
)


@pytest.fixture(autouse=True)
def reset_runtime_state():
    """
    Reset runtime and PostgreSQL domain state before every API test.

    Sprint-038:
    DairyOS now uses PostgreSQL as the single persistence backend.
    Tests must therefore explicitly isolate persistent domain data.

    The production runtime is never reset by this fixture.
    """

    # --------------------------------------------------------------
    # Reset persistent operational journal
    # --------------------------------------------------------------

    journal = PersistentEventJournal()
    journal.clear()

    container.event_journal = journal

    # --------------------------------------------------------------
    # Reset PostgreSQL domain data used by this API suite
    # --------------------------------------------------------------

    session = SessionLocal()

    try:
        # Milking schedule history references Animal, so delete it
        # before deleting animals.
        session.query(
            AnimalMilkingScheduleHistory
        ).delete(
            synchronize_session=False
        )

        session.query(
            Animal
        ).delete(
            synchronize_session=False
        )

        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()

    # --------------------------------------------------------------
    # Reset runtime projections/services
    # --------------------------------------------------------------

    container.farm_operational_state_service = (
        FarmOperationalStateService()
    )

    container.stop()

    container.operations = None

    container.dashboard = None


client = TestClient(app)


def test_create_animal():

    response = client.post(
        "/farm/animals",
        json={
            "animal_id": "TEST-COW-A1",
            "animal_type": "COW",
            "breed": "Sahiwal",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": "THRICE_DAILY",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["animal_id"] == "TEST-COW-A1"
    assert body["lifecycle_status"] == "LACTATING"
    assert body["is_currently_milking"] is True
    assert body["milking_frequency"] == "THRICE_DAILY"
    assert body["active"] is True


def test_create_duplicate_animal_rejected():

    client.post(
        "/farm/animals",
        json={
            "animal_id": "TEST-COW-DUP",
            "animal_type": "COW",
            "lifecycle_status": "LACTATING",
        },
    )

    response = client.post(
        "/farm/animals",
        json={
            "animal_id": "TEST-COW-DUP",
            "animal_type": "COW",
            "lifecycle_status": "LACTATING",
        },
    )

    assert response.status_code == 409


def test_create_animal_invalid_lifecycle_status_rejected():

    response = client.post(
        "/farm/animals",
        json={
            "animal_id": "TEST-COW-BAD",
            "animal_type": "COW",
            "lifecycle_status": "NOT_A_REAL_STATUS",
        },
    )

    assert response.status_code == 422


def test_get_animal():

    client.post(
        "/farm/animals",
        json={
            "animal_id": "TEST-COW-A2",
            "animal_type": "COW",
            "lifecycle_status": "LACTATING",
        },
    )

    response = client.get(
        "/farm/animals/TEST-COW-A2"
    )

    assert response.status_code == 200
    assert response.json()["animal_id"] == "TEST-COW-A2"


def test_get_nonexistent_animal_404():

    response = client.get(
        "/farm/animals/DOES-NOT-EXIST"
    )

    assert response.status_code == 404


def test_list_animals():

    response = client.get(
        "/farm/animals"
    )

    assert response.status_code == 200
    assert isinstance(
        response.json(),
        list,
    )


def test_list_currently_milking_animals():

    client.post(
        "/farm/animals",
        json={
            "animal_id": "TEST-COW-MILKING",
            "animal_type": "COW",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": "TWICE_DAILY",
        },
    )

    response = client.get(
        "/farm/animals?currently_milking=true"
    )

    assert response.status_code == 200

    animal_ids = [
        animal["animal_id"]
        for animal in response.json()
    ]

    assert "TEST-COW-MILKING" in animal_ids


def test_change_milking_frequency_confirmed_flow():
    """
    Confirmed requirement: milking frequency is per-animal and changes
    over the lactation cycle (e.g. tail-end animals dropping from 3x
    to 2x). This must be tracked with full history, not silently
    overwritten.
    """

    client.post(
        "/farm/animals",
        json={
            "animal_id": "TEST-COW-FREQ",
            "animal_type": "COW",
            "lifecycle_status": "LACTATING",
            "milking_frequency": "THRICE_DAILY",
        },
    )

    response = client.post(
        "/farm/animals/TEST-COW-FREQ/milking-frequency",
        json={
            "milking_frequency": "TWICE_DAILY",
            "changed_by": "test-manager",
            "reason": "End of lactation cycle",
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["milking_frequency"]
        == "TWICE_DAILY"
    )

    history_response = client.get(
        "/farm/animals/TEST-COW-FREQ/milking-frequency/history"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 2

    # Most recent first.
    assert (
        history[0]["milking_frequency"]
        == "TWICE_DAILY"
    )

    assert history[0]["effective_to"] is None

    assert (
        history[0]["reason"]
        == "End of lactation cycle"
    )

    assert (
        history[1]["milking_frequency"]
        == "THRICE_DAILY"
    )

    assert history[1]["effective_to"] is not None


def test_change_milking_frequency_invalid_value_rejected():

    client.post(
        "/farm/animals",
        json={
            "animal_id": "TEST-COW-FREQ-BAD",
            "animal_type": "COW",
            "lifecycle_status": "LACTATING",
        },
    )

    response = client.post(
        "/farm/animals/TEST-COW-FREQ-BAD/milking-frequency",
        json={
            "milking_frequency": "FOUR_TIMES_DAILY",
        },
    )

    assert response.status_code == 422


