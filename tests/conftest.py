import uuid

import pytest
from fastapi.testclient import TestClient

from dairyos.app import app, container
from dairyos.data.database.session import create_application_session
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.milk_production import MilkProduction
from dairyos.runtime.persistent_event_journal import PersistentEventJournal
from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)
from dairyos.farm.herd.services.animal_event_projection import AnimalEventProjection
from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)


def _reset_test_persistence() -> None:
    """Isolate API tests from durable records created by earlier tests.

    The application intentionally uses real persisted SQL data. The test
    client fixture therefore must clear mutable operational tables before
    each test; otherwise a cost-of-production test can accidentally include
    financial or milk records created by an unrelated earlier test.
    """

    session = create_application_session()
    try:
        session.query(FinancialTransaction).delete(synchronize_session=False)
        session.query(MilkProduction).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def client(tmp_path):
    journal = PersistentEventJournal()
    journal.clear()
    _reset_test_persistence()

    container.event_journal = journal
    container.animal_operational_state_repository = AnimalOperationalStateRepository(
        storage_path=tmp_path / "animal_operational_states.json"
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
            "animal_type": "COW",
            "breed": "Sahiwal",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": "THRICE_DAILY",
            "ear_tag": f"TEST-{uuid.uuid4().hex[:10].upper()}",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["system_generated_animal_id"] is True
    assert payload["animal_id"].startswith("AN-")
    return payload["animal_id"]
