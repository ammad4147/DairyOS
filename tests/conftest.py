import uuid

import pytest
from fastapi.testclient import TestClient

from dairyos.app import app, container

from dairyos.runtime.persistent_event_journal import PersistentEventJournal

from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)

from dairyos.farm.herd.services.animal_event_projection import (
    AnimalEventProjection,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)


@pytest.fixture()
def client(tmp_path):
    journal = PersistentEventJournal()
    journal.clear()

    container.event_journal = journal
    container.animal_operational_state_repository = (
        AnimalOperationalStateRepository(
            storage_path=tmp_path / "animal_operational_states.json"
        )
    )
    container.animal_event_projection = AnimalEventProjection(
        repository=container.animal_operational_state_repository
    )
    container.farm_operational_state_service = FarmOperationalStateService(
        animal_projection=container.animal_event_projection
    )
    container.started = False
    container.operations = None
    container.dashboard = None

    print("FIXTURE RESET:", container.event_journal.count(), flush=True)

    with TestClient(app) as c:
        print("AFTER STARTUP:", container.event_journal.count(), flush=True)
        yield c


@pytest.fixture()
def registered_animal(client: TestClient):
    """Create a real persisted Animal Register record and return its permanent ID."""

    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "sex": "FEMALE",
            "breed": "HOLSTEIN",
            "lifecycle_status": "LACTATING",
            "date_of_birth": "2022-01-01",
            "ear_tag": f"TEST-{uuid.uuid4().hex[:10].upper()}",
        },
    )
    assert response.status_code in (200, 201), response.text
    payload = response.json()
    assert payload["system_generated_animal_id"] is True
    return payload["animal_id"]
