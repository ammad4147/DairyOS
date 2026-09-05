"""Shared API fixtures with a fail-closed disposable-database gate."""

import os
import re
import sys
from urllib.parse import unquote, urlsplit
import uuid

import pytest
from fastapi.testclient import TestClient


def _configured_database_url() -> str:
    explicit = os.getenv("DAIRYOS_DATABASE_URL")
    if explicit:
        return explicit
    host = os.getenv("DAIRYOS_DB_HOST", "localhost")
    port = os.getenv("DAIRYOS_DB_PORT", "5432")
    name = os.getenv("DAIRYOS_DB_NAME", "dairyos")
    user = os.getenv("DAIRYOS_DB_USER", "dairyos")
    password = os.getenv("DAIRYOS_DB_PASSWORD", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def _database_name(database_url: str) -> str:
    parsed = urlsplit(database_url)
    return unquote(parsed.path.rstrip("/").rsplit("/", 1)[-1]).lower()


def _assert_disposable_test_database(database_url: str, source: str) -> None:
    database_name = _database_name(database_url)
    parsed = urlsplit(database_url)
    github_ephemeral_database = (
        os.getenv("CI", "").lower() == "true"
        and os.getenv("GITHUB_ACTIONS", "").lower() == "true"
        and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    )
    if github_ephemeral_database:
        return
    if "test" in database_name and database_name not in {
        "dairyos",
        "dairyos_prod",
        "dairyos_production",
        "dairyos_staging",
    }:
        return
    sys.stderr.write(
        "\nREFUSING TO RUN DESTRUCTIVE TEST FIXTURES.\n"
        f"The {source} database name is '{database_name or '<missing>'}', not an "
        "unambiguous disposable test database. Set DAIRYOS_DATABASE_URL or "
        "DAIRYOS_DB_NAME to a dedicated database whose database name contains "
        "'test'. Credentials have intentionally not been displayed.\n\n"
    )
    raise SystemExit(1)


_assert_disposable_test_database(_configured_database_url(), "configured")

from dairyos.app import app, container
from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.database.models.operational_event_model import OperationalEventModel
from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.payroll import PayrollRecord
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.health_observation import HealthObservation
from dairyos.data.models.health_case import HealthCase
from dairyos.data.models.operational_finding import OperationalFinding
from dairyos.data.models.operational_finding_lifecycle_event import OperationalFindingLifecycleEvent
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
from dairyos.data.database import session as _db_session


_assert_disposable_test_database(str(_db_session.engine.url), "resolved engine")


# Importing the application constructs ApplicationRuntime, whose durable
# withdrawal hydration performs a read-only treatment query. SQLAlchemy
# leaves that read inside a transaction until it is explicitly ended. The
# application test harness must release that import-time transaction before
# destructive PostgreSQL integration tests attempt TRUNCATE.
container.repository_factory.rollback()


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
            PayrollRecord,
            MilkDisposition,
            MilkProduction,
            FeedRecord,
            HealthObservation,
            HealthCase,
            OperationalFindingLifecycleEvent,
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

    PersistentEventJournal().clear()

    if getattr(container, "animal_operational_state_repository", None) is not None:
        container.animal_operational_state_repository.clear()

    if getattr(container, "operational_input_repository", None) is not None:
        container.operational_input_repository.clear()

    container.runtime._operational_state_service = FarmOperationalStateService(
        repository=container.runtime.operational_state_repository,
        animal_projection=container.animal_event_projection,
    )

    container.farm_operational_state_service = container.runtime._operational_state_service
    container.operational_state_service = container.runtime._operational_state_service
    container.runtime._operational_state_event_subscriber.operational_state_service = (
        container.runtime._operational_state_service
    )
    container.runtime._operational_input_projection_bridge.state_service = (
        container.runtime._operational_state_service
    )

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
    container.runtime._operational_input_projection_bridge.state_service = (
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

        # The fixture deliberately does NOT install a bearer token globally.
        # API tests that need an authenticated identity establish one explicitly;
        # this preserves the ability to verify unauthenticated contracts such as
        # GET /me and GET /users while development-mode operational routes remain
        # usable by tests that exercise their legacy operator contract.
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
