"""
DairyOS PostgreSQL database initialization.

Sprint-038
==========

This module is the single database initialization boundary.

All SQLAlchemy ORM models must be imported here so that they are
registered with Base.metadata before create_all() executes.
"""

import os

from dairyos.data.database.base import Base
from dairyos.data.database.session import engine

# ------------------------------------------------------------------
# ORM model registration
# ------------------------------------------------------------------

from dairyos.data.models.animal import Animal

from dairyos.data.models.animal_milking_schedule_history import (
    AnimalMilkingScheduleHistory,
)

from dairyos.data.models.farm import Farm

from dairyos.data.models.feed_record import FeedRecord

from dairyos.data.models.financial_transaction import (
    FinancialTransaction,
)

from dairyos.data.database.models.breeding_record_model import (
    BreedingRecordModel,
)

from dairyos.data.models.breeding_propagation_outbox import (
    BreedingPropagationOutbox,
)

from dairyos.data.models.health_observation import (
    HealthObservation,
)

from dairyos.data.models.health_case import (
    HealthCase,
)

from dairyos.data.models.milk_production import (
    MilkProduction,
)

from dairyos.data.models.operational_finding import (
    OperationalFinding,
)

from dairyos.data.models.operational_finding_lifecycle_event import (
    OperationalFindingLifecycleEvent,
)

from dairyos.data.models.milk_disposition import (
    MilkDisposition,
)

from dairyos.data.models.milking_session_record import (
    MilkingSessionRecord,
)

from dairyos.data.database.models.operational_event_model import (
    OperationalEventModel,
)

from dairyos.data.database.models.operational_state_model import (
    OperationalStateModel,
)

from dairyos.data.database.models.event_journal_model import (
    EventJournalModel,
)

from dairyos.data.models.treatment_record import (
    TreatmentRecord,
)

from dairyos.data.models.drug_withdrawal_reference import (
    DrugWithdrawalReference,
)

from dairyos.data.models.inventory_transaction import (
    InventoryTransaction,
)
from dairyos.data.models.semen_inventory import (
    SemenLot,
    SemenStockMovement,
)

from dairyos.data.models.user import (
    User,
)


def initialize_database() -> None:
    """Create the development/test schema when explicitly appropriate.

    Production/staging/preprod startup is migration-owned. The Windows
    supervisor runs the migration gate before the application is constructed,
    so ``create_all()`` must never silently compete with Alembic in those
    environments.
    """
    environment = os.getenv("DAIRYOS_ENV", "development").strip().lower()
    if environment in {"production", "staging", "preprod"}:
        return

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialize_database()
    print("DairyOS PostgreSQL database initialized.")
