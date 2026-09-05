"""Guards against vocabulary drift between advertised and enforced values."""
from fastapi.testclient import TestClient
import pytest

from dairyos.app import app, container
from dairyos.runtime.persistent_event_journal import PersistentEventJournal
from dairyos.farm.operations.state.farm_operational_state_service import FarmOperationalStateService
from dairyos.data.database.session import SessionLocal
from dairyos.data.models.animal import Animal
from dairyos.data.models.animal_milking_schedule_history import AnimalMilkingScheduleHistory
from dairyos.data.models.milk_production import MilkProduction


@pytest.fixture(autouse=True)
def reset_runtime_state():
    journal = PersistentEventJournal()
    container.event_journal = journal

    session = SessionLocal()
    try:
        for model in (MilkProduction, AnimalMilkingScheduleHistory, Animal):
            for row in session.query(model).all():
                session.delete(row)
                session.flush()
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


def _advertised():
    response = client.get("/farm/reference-data")
    assert response.status_code == 200
    governed = response.json()["governed"]
    return set(governed["lifecycle_statuses"]), set(governed["milking_frequencies"])


def _sex_for_lifecycle(status: str) -> str:
    return "MALE" if status == "BULL" else "FEMALE"


def _create_animal(status: str):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "breed": "Sahiwal",
            "lifecycle_status": status,
            "sex": _sex_for_lifecycle(status),
        },
    )
    assert response.status_code == 200, response.json()
    return response


def test_every_advertised_lifecycle_status_is_accepted_on_registration():
    advertised, _ = _advertised()

    for status in advertised:
        response = _create_animal(status)
        assert response.json()["lifecycle_status"] == status


def test_every_advertised_lifecycle_status_is_accepted_on_lifecycle_change():
    advertised, _ = _advertised()

    # A single animal cannot legitimately move between BULL and female-only
    # lifecycle states because the canonical classification contract protects
    # sex/lifecycle integrity. Create a fresh biologically valid animal for
    # each advertised status instead of weakening that domain rule.
    for status in advertised:
        created = _create_animal("HEIFER")
        animal_id = created.json()["animal_id"]

        if status == "BULL":
            sex_response = client.patch(
                f"/farm/animals/{animal_id}",
                json={"sex": "MALE"},
            )
            assert sex_response.status_code == 200, sex_response.json()

        response = client.patch(
            f"/farm/animals/{animal_id}/lifecycle",
            json={"lifecycle_status": status},
        )
        assert response.status_code == 200, (
            f"{status!r} is advertised at GET /farm/reference-data but rejected "
            f"by PATCH /farm/animals/{{id}}/lifecycle: {response.json()}"
        )
        assert response.json()["lifecycle_status"] == status


def test_every_advertised_milking_frequency_is_accepted():
    _, advertised = _advertised()

    created = _create_animal("LACTATING")
    animal_id = created.json()["animal_id"]

    for frequency in advertised:
        response = client.post(
            f"/farm/animals/{animal_id}/milking-frequency",
            json={"milking_frequency": frequency},
        )
        assert response.status_code == 200, (
            f"{frequency!r} is advertised at GET /farm/reference-data but rejected "
            f"by POST /farm/animals/{{id}}/milking-frequency: {response.json()}"
        )
        assert response.json()["milking_frequency"] == frequency


def test_sold_and_deceased_are_now_reachable():
    for status in ("SOLD", "DECEASED", "CULLED"):
        response = _create_animal(status)
        assert response.json()["lifecycle_status"] == status


def test_sick_is_no_longer_a_lifecycle_status():
    response = client.post(
        "/farm/animals",
        json={"animal_type": "COW", "breed": "Sahiwal", "lifecycle_status": "SICK"},
    )
    assert response.status_code == 422


def test_once_daily_milking_frequency_is_rejected():
    created = _create_animal("LACTATING")
    animal_id = created.json()["animal_id"]

    response = client.post(
        f"/farm/animals/{animal_id}/milking-frequency",
        json={"milking_frequency": "ONCE_DAILY"},
    )
    assert response.status_code == 422
