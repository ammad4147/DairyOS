"""Prepare a DairyOS deployment database for zero operational state.

The command is intentionally dry-run by default. It preserves system/master
configuration and user accounts, and reports the operational tables that would
be truncated. Execution requires both ``--execute`` and the explicit
``--confirm-zero-state`` flag. This is meant for the final deployment database,
not the active development database.
"""
from __future__ import annotations

import argparse
import os

from sqlalchemy import inspect, text

from dairyos.data.database.session import engine

PRESERVE_EXACT = {
    "users",
    "app_settings",
    "drug_withdrawal_references",
    "drug_references",
    "alembic_version",
}
PRESERVE_MARKERS = (
    "reference",
    "taxonomy",
    "setting",
    "config",
    "permission",
    "role",
)


def is_preserved(table: str) -> bool:
    lowered = table.lower()
    return lowered in PRESERVE_EXACT or any(marker in lowered for marker in PRESERVE_MARKERS)


def candidate_tables() -> list[str]:
    inspector = inspect(engine)
    return sorted(name for name in inspector.get_table_names() if not is_preserved(name))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Actually truncate operational tables.")
    parser.add_argument("--confirm-zero-state", action="store_true", help="Required confirmation for destructive execution.")
    args = parser.parse_args()

    tables = candidate_tables()
    print("DairyOS deployment zero-state utility")
    print("Database:", os.getenv("DAIRYOS_DATABASE_URL") or "DAIRYOS_DB_* configuration")
    print("Preserved: users, application settings, reference/master/configuration tables")
    print("Operational tables identified:")
    for table in tables:
        print("  -", table)

    if not args.execute:
        print("\nDRY RUN ONLY. No database changes were made.")
        print("Review the list, then rerun with --execute --confirm-zero-state on the deployment database.")
        return 0

    if not args.confirm_zero_state:
        raise SystemExit("Refusing destructive execution without --confirm-zero-state.")

    with engine.begin() as connection:
        if tables:
            quoted = ", ".join(f'"{table}"' for table in tables)
            connection.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))

    print("\nZERO-STATE RESET COMPLETE.")
    print("Preserved system/reference configuration and user accounts.")
    print("Operational transactions and identifiers were reset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
