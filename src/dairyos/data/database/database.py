"""
DairyOS PostgreSQL database initialization.

Sprint-038
==========

This module is the single database initialization boundary.

All SQLAlchemy ORM models must be imported here so that they are
registered with Base.metadata before create_all() executes.
"""

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

from dairyos.data.models.health_observation import (
    HealthObservation,
)

from dairyos.data.models.milk_production import (
    MilkProduction,
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


def initialize_database() -> None:
    """
    Create all registered PostgreSQL tables if they do not exist.

    The operation is intentionally idempotent.

    Schema evolution belongs to the migration layer, not to this
    runtime initialization boundary.
    """

    Base.metadata.create_all(
        bind=engine,
    )


if __name__ == "__main__":
    initialize_database()

    print(
        "DairyOS PostgreSQL database initialized."
    )
