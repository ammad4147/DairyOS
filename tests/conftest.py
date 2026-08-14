import uuid

import pytest
from fastapi.testclient import TestClient

from dairyos.app import app, container
from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.health_observation import HealthObservation
from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.milking_session_record import MilkingSessionRecord
from dairyos.data.models.user import User
from dairyos.runtime.persistent_event_journal import PersistentEventJournal
from dairyos.farm.herd.repository.animal_operational_state_repository import (
    AnimalOperationalStateRepository,
)
from dairyos.farm.herd.services.animal_event_projection import AnimalEventProjection
from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)


def _reset_test_persistence() -> None:
    """Isolate API tests from durable operational records created by earlier tests.

    DairyOS intentionally uses real persisted SQL repositories. The reset is
    performed after the application runtime has started so cleanup targets the
    exact repository/session composition used by the API under test. Every
    persisted repository consumed by the KPI and cost engines is cleared,
    including the operational breeding repository. Welfare observations share
    the operational-state repository, so only that persisted observation
    collection is removed here; unrelated operational state remains intact.
    """

    factory = container.repository_factory
    session = factory.session
    session.rollback()

    try:
        for model in (
            FinancialTransaction,
            MilkProduction,
            FeedRecord,
            HealthObservation,
            InventoryTransaction,
            User,
            BreedingRecordModel,
            # The session ledger MUST be cleared alongside MilkProduction.
            # Sequencing reads the ledger, so a row left behind by one test
            # silently changes what the next test is allowed to record.
            MilkingSessionRecord,
        ):
            session.query(model).delete(synchronize_session=False)

        operational_models = session.query(OperationalStateModel).all()
        for model in operational_models:
            payload = dict(model.state_payload or {})
            if "animal_welfare_observations" in payload:
                payload.pop("animal_welfare_observations", None)
                model.state_payload = payload

        session.commit()
        session.expire_all()
    except Exception:
        session.rollback()
        raise


@pytest.fixture()
def client(tmp_path):
    journal = PersistentEventJournal()
    journal.clear()

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
    container.operational_input_repository.clear()
    container.started = False
    container.operations = None
    container.dashboard = None

    with TestClient(app) as c:
        # Reset only after RuntimeContainer.start() has installed the active
        # repository factory, preventing stale-session cleanup from leaving
        # persisted KPI inputs visible to the next test.
        _reset_test_persistence()
        print("FIXTURE RESET:", container.event_journal.count(), flush=True)
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
