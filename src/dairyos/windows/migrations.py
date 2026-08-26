"""Safe startup migration gate for the packaged DairyOS runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, create_engine, inspect, text

from dairyos.lifecycle.manager import LifecycleManager
from dairyos.platform import paths


MIGRATION_LOCK_KEY = 746182934517


class MigrationGateError(RuntimeError):
    """Raised when the database cannot safely reach the packaged schema head."""


@dataclass(frozen=True)
class MigrationResult:
    migrated: bool
    current_heads: tuple[str, ...]
    target_heads: tuple[str, ...]
    backup_path: Path | None = None


def _find_alembic_ini() -> Path:
    override = os.environ.get("DAIRYOS_ALEMBIC_INI")
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override).expanduser())

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "alembic.ini")

    here = Path(__file__).resolve()
    repo_root = here.parents[2]
    candidates.append(repo_root / "alembic.ini")
    candidates.append(Path.cwd() / "alembic.ini")

    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate.is_file():
            return candidate
    raise MigrationGateError("DairyOS Alembic configuration was not found in the packaged runtime.")


def _build_config() -> tuple[Config, ScriptDirectory]:
    ini = _find_alembic_ini()
    config = Config(str(ini))
    script_location = ini.parent / "db_migrations"
    if not script_location.is_dir():
        raise MigrationGateError(f"DairyOS migration scripts are missing: {script_location}")
    config.set_main_option("script_location", str(script_location))
    return config, ScriptDirectory.from_config(config)


def _database_url() -> str:
    """Resolve the database URL from the current environment on every call."""
    try:
        from dairyos.data.database.session import _build_database_url
    except Exception as exc:
        raise MigrationGateError(f"Unable to resolve the DairyOS database configuration: {exc}") from exc
    try:
        url = _build_database_url()
    except Exception as exc:
        raise MigrationGateError(f"DairyOS database configuration is invalid: {exc}") from exc
    if not url:
        raise MigrationGateError("DairyOS database configuration is empty.")
    return url


def _reconcile_untracked_database(
    connection: Connection, config: Config, target: tuple[str, ...]
) -> MigrationResult | None:
    """Reconcile a database with no Alembic history without guessing.

    This repository's migration history is incremental-only: the revisions
    assume the baseline ORM tables already exist. Therefore an empty database
    is initialized from the authoritative ORM metadata and stamped at the
    packaged Alembic heads. A non-empty database with no Alembic history is
    only stamped when every expected ORM table and column is already present;
    an incomplete schema is rejected rather than silently hidden by a stamp.
    """
    config.attributes["connection"] = connection
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())

    from dairyos.data.database.database import Base

    if not existing_tables:
        Base.metadata.create_all(bind=connection)
        command.stamp(config, "heads")
        return MigrationResult(True, (), target, backup_path=None)

    expected_tables = {table.name for table in Base.metadata.sorted_tables}
    missing_tables = expected_tables - existing_tables
    if missing_tables:
        raise MigrationGateError(
            "This database has tables but no Alembic migration history "
            "(likely created by an earlier version of DairyOS outside the "
            "migration gate), and it is missing tables the current version "
            f"expects: {sorted(missing_tables)}. Refusing to guess -- this "
            "needs a manual review rather than an automatic stamp. Back up "
            "this database, then either restore a known-good backup or have "
            "someone familiar with the schema reconcile it by hand."
        )

    mismatches: list[str] = []
    for table in Base.metadata.sorted_tables:
        actual_columns = {column["name"] for column in inspector.get_columns(table.name)}
        expected_columns = {column.name for column in table.columns}
        missing = expected_columns - actual_columns
        if missing:
            mismatches.append(f"{table.name}: missing columns {sorted(missing)}")

    if mismatches:
        raise MigrationGateError(
            "This database has tables but no Alembic migration history, "
            "and its columns do not match what the current version of "
            "DairyOS expects:\n  " + "\n  ".join(mismatches) + "\n"
            "Refusing to guess -- back up this database, then either restore "
            "a known-good backup or reconcile it by hand before DairyOS will start."
        )

    command.stamp(config, "heads")
    return MigrationResult(True, (), target, backup_path=None)


def migrate_if_needed() -> MigrationResult:
    """Backup and migrate only when the database is behind the packaged head.

    A PostgreSQL transaction-level advisory lock serializes migration checks
    across processes. The same SQLAlchemy connection is handed to Alembic so
    the lock remains active for the actual migration transaction. A verified
    pre-migration backup is created before any schema change. Databases with
    no Alembic history are reconciled safely before the normal upgrade path.
    """
    database_url = _database_url()
    config, script = _build_config()
    engine = create_engine(database_url, pool_pre_ping=True)
    backup_path: Path | None = None

    try:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(:lock_key)"),
                {"lock_key": MIGRATION_LOCK_KEY},
            )
            migration_context = MigrationContext.configure(connection)
            current = tuple(sorted(migration_context.get_current_heads()))
            target = tuple(sorted(script.get_heads()))

            if current == target:
                return MigrationResult(False, current, target)

            if not current:
                reconciled = _reconcile_untracked_database(connection, config, target)
                if reconciled is not None:
                    return reconciled

            manager = LifecycleManager(
                installation_root=Path(sys.executable).resolve().parent,
                data_root=paths.data_root(create=True),
                database_url=database_url,
            )
            try:
                backup_path = manager.backup(label="pre-migration")
            except Exception as exc:
                raise MigrationGateError(
                    f"Pre-migration backup failed; startup is blocked: {exc}"
                ) from exc

            config.attributes["connection"] = connection
            try:
                command.upgrade(config, "heads")
            except Exception as exc:
                raise MigrationGateError(
                    "DairyOS database migration failed. Startup is blocked. "
                    f"Pre-migration backup: {backup_path}. Original error: {exc}"
                ) from exc

            verification = MigrationContext.configure(connection)
            final_heads = tuple(sorted(verification.get_current_heads()))
            if final_heads != target:
                raise MigrationGateError(
                    "DairyOS migration completed without reaching all expected heads. "
                    f"Expected {target}; found {final_heads}. Backup: {backup_path}"
                )

            return MigrationResult(True, current, target, backup_path)
    except MigrationGateError:
        raise
    except Exception as exc:
        raise MigrationGateError(
            f"DairyOS database preflight failed; startup is blocked: {exc}"
        ) from exc
    finally:
        engine.dispose()
