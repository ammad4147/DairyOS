"""
Database initialization compatibility entry point.

Sprint-038
==========

The canonical database initialization boundary lives in:

    dairyos.data.database.database.initialize_database

This module remains as a compatibility entry point for callers that
still import or execute:

    dairyos.data.database.initialize
"""

from dairyos.data.database.database import initialize_database


if __name__ == "__main__":
    initialize_database()

    print(
        "DairyOS PostgreSQL database initialized."
    )
