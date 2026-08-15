"""Guards against the vocabulary-drift class of defect (Phase 1, 2026-08-14).

Before this fix, three independent lists governed animal lifecycle_status
(reference_data.py's advertised GOVERNED list, animal_registration.py's write
validation, animal_management/router.py's write validation) and disagreed:
SOLD/DECEASED were advertised but always rejected on write (no way to retire
an animal), while CLOSE_UP/SICK were accepted on write but never advertised.
milking_frequency had the same shape: ONCE_DAILY was offered in the frontend
dropdown but not validated by any write path and not supported by the milk
session sequencing service.

These tests assert the advertised (GET /farm/reference-data) and enforced
(both write paths) sets are identical, so this class of defect cannot
silently reopen.
"""
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
    journal.clear()
    container.event_journal = journal

    session = SessionLocal()
    try:
        # MilkProduction now has a foreign-key dependency on Animal. Remove
        # dependent rows before resetting the Animal register so the fixture
        # remains valid against the canonical schema.
        session.query(MilkProduction).delete(synchronize_session=False)
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


def _advertised():
    response = client.get("/farm/reference-data")
    assert response.status_code == 200
    governed = response.json()["governed"]
    return set(governed["lifecycle_statuses"]), set(governed["milking_frequencies"])


def test_every_advertised_lifecycle_status_is_accepted_on_registration():
    advertised, _ = _advertised()

    for status in advertised:
        response = client.post(
            "/farm/animals",
            json={"animal_type": "COW", "breed": "Sahiwal", "lifecycle_status": status},
        )
        assert response.status_code == 200, (
            f"{status!r} is advertised at GET /farm/reference-data but rejected "
            f"by POST /farm/animals: {response.json()}"
        )
        assert response.json()["lifecycle_status"] == status


def test_every_advertised_lifecycle_status_is_accepted_on_lifecycle_change():
    advertised, _ = _advertised()

    created = client.post(
        "/farm/animals",
        json={"animal_type": "COW", "breed": "Sahiwal", "lifecycle_status": "HEIFER"},
    )
    animal_id = created.json()["animal_id"]

    for status in advertised:
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

    created = client.post(
        "/farm/animals",
        json={"animal_type": "COW", "breed": "Sahiwal", "lifecycle_status": "LACTATING"},
    )
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
    """The concrete animal-retirement-path regression this fix closes."""
    for status in ("SOLD", "DECEASED", "CULLED"):
        response = client.post(
            "/farm/animals",
            json={"animal_type": "COW", "breed": "Sahiwal", "lifecycle_status": status},
        )
        assert response.status_code == 200
        assert response.json()["lifecycle_status"] == status


def test_sick_is_no_longer_a_lifecycle_status():
    """Domain decision 2026-08-14: SICK is a health condition, not a life
    stage, and is dropped from lifecycle_status pending HealthCase (G5.1)."""
    response = client.post(
        "/farm/animals",
        json={"animal_type": "COW", "breed": "Sahiwal", "lifecycle_status": "SICK"},
    )
    assert response.status_code == 422


def test_once_daily_milking_frequency_is_rejected():
    """MilkSessionSequenceService has no branch for ONCE_DAILY; removed from
    the advertised/enforced vocabulary rather than left silently unsupported."""
    created = client.post(
        "/farm/animals",
        json={"animal_type": "COW", "breed": "Sahiwal", "lifecycle_status": "LACTATING"},
    )
    animal_id = created.json()["animal_id"]

    response = client.post(
        f"/farm/animals/{animal_id}/milking-frequency",
        json={"milking_frequency": "ONCE_DAILY"},
    )
    assert response.status_code == 422
