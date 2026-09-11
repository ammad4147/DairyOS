"""
DairyOS PostgreSQL database initialization.

Sprint-038
==========

This module is the single database initialization boundary.

All SQLAlchemy ORM models must be imported here so that they are
registered with Base.metadata before create_all() executes.
"""

import os
import sys

from dairyos.data.database.base import Base
from dairyos.data.database.session import engine

# ------------------------------------------------------------------
# ORM model registration
# ------------------------------------------------------------------

from dairyos.data.models.animal import Animal

from dairyos.data.models.animal_milking_schedule_history import (
    AnimalMilkingScheduleHistory,
)

from dairyos.data.database.models.farm_model import (
    FarmModel,
)

from dairyos.data.models.equipment import (
    Equipment,
    EquipmentServiceEvent,
)

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
from dairyos.data.models.operational_write import (
    OperationalWrite,
    OperationalProjectionOutbox,
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

from dairyos.data.models.milk_production_correction import (
    MilkProductionCorrection,
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
from dairyos.data.models.vaccination_record import VaccinationRecord

from dairyos.data.models.user import (
    User,
)

from dairyos.data.models.ai_assistant_conversation import (
    AIAssistantConversationModel,
    AIAssistantMessageModel,
)


def initialize_database() -> None:
    """Create the development/test schema when explicitly appropriate.

    Production/staging/preprod startup is migration-owned. The Windows
    supervisor runs the migration gate before the application is constructed,
    so ``create_all()`` must never silently compete with Alembic in those
    environments.
    """
    # A frozen DairyOS executable is always migration-owned.
    # Packaged production must never fall back to development create_all()
    # merely because DAIRYOS_ENV was absent, stale, or not inherited.
    if bool(getattr(sys, "frozen", False)):
        return

    environment = os.getenv("DAIRYOS_ENV", "development").strip().lower()
    if environment in {"production", "staging", "preprod"}:
        return

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialize_database()
    print("DairyOS PostgreSQL database initialized.")
