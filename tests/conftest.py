import re
import uuid

import pytest
from fastapi.testclient import TestClient

from dairyos.app import app, container
from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.database.models.operational_event_model import OperationalEventModel
from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.health_observation import HealthObservation
from dairyos.data.models.health_case import HealthCase
from dairyos.data.models.operational_finding import OperationalFinding
from dairyos.data.models.app_setting import AppSetting
from dairyos.data.models.animal import Animal
from dairyos.data.models.animal_milking_schedule_history import AnimalMilkingScheduleHistory
from dairyos.data.models.treatment_record import TreatmentRecord
from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.milk_disposition import MilkDisposition
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
    """Create a clean durable persistence boundary for every API test."""

    factory = container.repository_factory
    session = factory.session
    session.rollback()

    try:
        # Dependency order: child/ledger tables first, then primary
        # domain registers and operational projections.
        for model in (
            FinancialTransaction,
            MilkDisposition,
            MilkProduction,
            FeedRecord,
            HealthObservation,
            HealthCase,
            OperationalFinding,
            InventoryTransaction,
            User,
            BreedingRecordModel,
            MilkingSessionRecord,
            AppSetting,
            TreatmentRecord,
            AnimalMilkingScheduleHistory,
            Animal,
            OperationalEventModel,
            OperationalStateModel,
            EventJournalModel,
        ):
            session.query(model).delete(synchronize_session=False)

        session.commit()
        session.expire_all()

    except Exception:
        session.rollback()
        raise

    # The event journal owns its own short-lived sessions. Clear it again
    # explicitly so the application replay boundary is unquestionably empty.
    PersistentEventJournal().clear()

    # Clear non-SQL projections used by the application runtime.
    if getattr(container, "animal_operational_state_repository", None) is not None:
        container.animal_operational_state_repository.clear()

    if getattr(container, "operational_input_repository", None) is not None:
        container.operational_input_repository.clear()

    # Recreate the persisted operational-state application service so no
    # FarmOperationalState object survives from a previous test.
    container.runtime._operational_state_service = FarmOperationalStateService(
        repository=container.runtime.operational_state_repository,
        animal_projection=container.animal_event_projection,
    )

    container.farm_operational_state_service = container.runtime._operational_state_service
    container.operational_state_service = container.runtime._operational_state_service

    # Rebind the event subscriber to the fresh service.
    container.runtime._operational_state_event_subscriber.operational_state_service = (
        container.runtime._operational_state_service
    )

    # Force the compatibility facade to rebuild its runtime surfaces on the
    # next TestClient startup.
    container.started = False
    container.operations = None
    container.dashboard = None


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

    container.operational_input_repository.clear()

    container.started = False
    container.operations = None
    container.dashboard = None

    # Rebind the runtime's animal projection to the test-local projection.
    container.runtime._animal_operational_state_repository = (
        container.animal_operational_state_repository
    )
    container.runtime._animal_event_projection = container.animal_event_projection

    container.runtime._operational_state_service = FarmOperationalStateService(
        repository=container.runtime.operational_state_repository,
        animal_projection=container.animal_event_projection,
    )
    container.farm_operational_state_service = container.runtime._operational_state_service
    container.operational_state_service = container.runtime._operational_state_service
    container.runtime._operational_state_event_subscriber.operational_state_service = (
        container.runtime._operational_state_service
    )

    with TestClient(app) as c:
        _reset_test_persistence()

        from dairyos.operations.intelligence.services.withdrawal_service import (
            WithdrawalService,
        )

        withdrawal_service = WithdrawalService()
        container.runtime._withdrawal_service = withdrawal_service
        container.withdrawal_service = withdrawal_service

        # Production API routes are intentionally authenticated. The test
        # fixture therefore establishes the same bearer identity that a real
        # client must establish instead of bypassing authorization middleware.
        login = c.post(
            "/auth/login",
            json={"username": "admin", "password": "dairyos"},
        )
        assert login.status_code == 200, login.text
        access_token = login.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {access_token}"})

        print(
            "FIXTURE RESET EVENT JOURNAL:",
            container.event_journal.count(),
            flush=True,
        )

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
    assert re.match(r"^[A-Z]{1,6}-\d{3,}$", payload["animal_id"]), payload["animal_id"]
    return payload["animal_id"]


# ---------------------------------------------------------------------------
# SESSION-END PERSISTENCE CLEANUP
# ---------------------------------------------------------------------------
# API fixtures already reset persistence before each test. This finalizer
# guarantees that the COMPLETE pytest session also leaves the database and
# persistent event journal clean, including tests that never request `client`.
#
# This is intentionally test-only. It does not alter production persistence
# behavior or the /settings/reset-test-data endpoint.
@pytest.fixture(scope="session", autouse=True)
def _cleanup_persistence_after_test_session():
    yield

    try:
        _reset_test_persistence()
    finally:
        PersistentEventJournal().clear()

        if getattr(container, "animal_operational_state_repository", None) is not None:
            container.animal_operational_state_repository.clear()

        if getattr(container, "operational_input_repository", None) is not None:
            container.operational_input_repository.clear()

        container.started = False
        container.operations = None
        container.dashboard = None
