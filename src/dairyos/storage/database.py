"""
DairyOS storage compatibility facade.

Sprint-038
==========

PostgreSQL + SQLAlchemy is the single persistence backend.

Historically this module provided a SQLite database implementation
for the persistent event journal. That implementation has now been
removed from the operational architecture.

This module remains temporarily as a compatibility boundary for
legacy callers while persistence is consolidated around the
SQLAlchemy database layer.

New code should use:

    dairyos.data.database.session

and:

    dairyos.data.database.database

directly.
"""

from sqlalchemy.engine import Connection

from dairyos.data.database.database import (
    initialize_database as _initialize_database,
)
from dairyos.data.database.session import (
    engine,
    get_session,
)


def initialize_database() -> None:
    """
    Initialize the DairyOS PostgreSQL schema.

    This delegates to the single SQLAlchemy database initializer.
    """

    _initialize_database()


def get_connection() -> Connection:
    """
    Compatibility connection boundary.

    Returns a SQLAlchemy connection backed by PostgreSQL.

    New application code should prefer a SQLAlchemy Session rather
    than calling this function directly.
    """

    return engine.connect()


__all__ = [
    "engine",
    "get_session",
    "get_connection",
    "initialize_database",
]
