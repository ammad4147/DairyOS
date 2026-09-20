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
