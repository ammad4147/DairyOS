"""Canonical, transactional DairyOS operational-data reset boundary."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile

import sqlalchemy as sa
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import NullPool

from dairyos.lifecycle.manager import LifecycleError
from dairyos.platform import paths

PRESERVED_TABLES = frozenset(
    {
        "alembic_version",
        "app_settings",
        "users",
        "drug_withdrawal_reference",
        "email_sender_settings",
    }
)

DEPLOYMENT_ACTIVE_KEY = "deployment_activated"
RESET_LOCK_TIMEOUT = "10s"
RESET_STATEMENT_TIMEOUT = "60s"
FILE_PROJECTION_FILENAMES = (
    "operational_inputs.json",
    "animal_operational_states.json",
)


@dataclass(frozen=True)
class ResetExecution:
    tables_cleared: tuple[str, ...]


def reset_operational_data(
    database_url: str,
    *,
    updated_by: str,
    data_root: str | Path | None = None,
) -> ResetExecution:
    """Deactivate deployment and clear every operational authority.

    This is deliberately a lifecycle primitive rather than an application API.
    The caller is responsible for creating and verifying the external recovery
    snapshot before invoking this function.

    The preserved ``app_settings`` table is updated directly through the same
    SQL transaction as the operational-table truncation. The reset engine uses
    ``NullPool`` so no connection is retained after the lifecycle operation.
    The destructive statement targets only the explicitly non-preserved tables;
    it deliberately does not use ``CASCADE`` because preserved tables must
    never be deleted implicitly by Reset. The two event-owned JSON files are
    also reset to empty projections after the database transaction commits.
    They are not independent operational authorities and must not retain
    records from before the reset.
    """
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        inspector = inspect(engine)
        tables = tuple(
            sorted(
                table
                for table in inspector.get_table_names()
                if table not in PRESERVED_TABLES
            )
        )

        with engine.begin() as connection:
            connection.execute(sa.text("SET LOCAL lock_timeout = '10s'"))
            connection.execute(sa.text("SET LOCAL statement_timeout = '60s'"))
            if connection.dialect.name == "postgresql":
                # The database trigger is an independent circuit breaker. The
                # lifecycle path explicitly opts in only after the caller has
                # resolved the protected administrative database identity;
                # the trigger still rejects this setting for ordinary roles.
                connection.execute(
                    sa.text("SET LOCAL dairyos.allow_destructive_op = 'true'")
                )

            connection.execute(
                sa.text(
                    "INSERT INTO app_settings "
                    "(key, value, updated_at, updated_by) "
                    "VALUES (:key, 'false', CURRENT_TIMESTAMP, :updated_by) "
                    "ON CONFLICT (key) DO UPDATE SET "
                    "value='false', updated_at=CURRENT_TIMESTAMP, updated_by=:updated_by"
                ),
                {
                    "key": DEPLOYMENT_ACTIVE_KEY,
                    "updated_by": updated_by,
                },
            )

            if tables:
                quoted = ", ".join(
                    '"' + table.replace('"', '""') + '"' for table in tables
                )
                connection.execute(sa.text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY"))

        # The database is authoritative, but these two files are durable read
        # models which can otherwise make a fresh database appear populated on
        # the next process start. Clear them as part of the same lifecycle
        # operation; a caller with a verified pre-reset backup can roll back if
        # the filesystem boundary fails.
        clear_file_projections(data_root)

        remaining = verify_zero_state(database_url)
        remaining.update(verify_file_projection_zero_state(data_root))
        if remaining:
            raise LifecycleError(
                "Reset zero-state verification failed: "
                + ", ".join(
                    f"{table}={count}" for table, count in sorted(remaining.items())
                )
            )

        return ResetExecution(tables_cleared=tables)
    finally:
        engine.dispose()


def verify_zero_state(database_url: str) -> dict[str, int]:
    """Return non-preserved tables that still contain rows."""
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        remaining: dict[str, int] = {}
        inspector = inspect(engine)
        with engine.connect() as connection:
            for table in inspector.get_table_names():
                if table in PRESERVED_TABLES:
                    continue
                quoted = '"' + table.replace('"', '""') + '"'
                count = int(
                    connection.execute(
                        sa.text(f"SELECT count(*) FROM {quoted}")
                    ).scalar_one()
                )
                if count:
                    remaining[table] = count
        return remaining
    finally:
        engine.dispose()


def _projection_paths(data_root: str | Path | None) -> tuple[Path, ...]:
    root = (
        Path(data_root).expanduser().resolve()
        if data_root is not None
        else paths.data_root(create=False).resolve()
    )
    storage = root / "storage"
    return tuple(storage / filename for filename in FILE_PROJECTION_FILENAMES)


def _write_empty_projection(path: Path) -> None:
    """Atomically replace one event-owned projection with an empty list."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".reset-tmp",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump([], stream)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def clear_file_projections(data_root: str | Path | None = None) -> tuple[str, ...]:
    """Remove pre-reset operational records from rebuildable JSON projections."""
    paths_cleared: list[str] = []
    for path in _projection_paths(data_root):
        _write_empty_projection(path)
        paths_cleared.append(str(path))
    return tuple(paths_cleared)


def verify_file_projection_zero_state(
    data_root: str | Path | None = None,
) -> dict[str, int]:
    """Return non-empty or malformed event-owned projections."""
    remaining: dict[str, int] = {}
    for path in _projection_paths(data_root):
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            remaining[path.name] = 1
            continue
        count = len(payload) if isinstance(payload, list) else 1
        if count:
            remaining[path.name] = count
    return remaining
