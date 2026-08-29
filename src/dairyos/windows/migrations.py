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
from sqlalchemy import create_engine, text

from dairyos.lifecycle.manager import LifecycleManager
from dairyos.platform import paths
from dairyos.windows.startup_integrity import (
    StartupIntegrityError,
    inspect_startup_integrity,
)


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


def _public_application_table_count(connection) -> int:
    """Return the number of non-Alembic tables in PostgreSQL's public schema."""
    result = connection.execute(
        text(
            """
            SELECT count(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
              AND table_name <> 'alembic_version'
            """
        )
    )
    return int(result.scalar_one())


def _bootstrap_empty_database(connection, config: Config, target: tuple[str, ...]) -> None:
    """Create the current ORM schema once for a genuinely empty database.

    Production remains migration-owned: the normal application initializer
    still refuses to call ``create_all()`` in production. This explicit empty-
    database bootstrap belongs to the migration gate and is immediately
    recorded at the current Alembic head. Non-empty databases without history
    are still rejected rather than guessed at.
    """
    from dairyos.data.database.base import Base
    import dairyos.data.database.database  # noqa: F401  # registers all ORM models

    Base.metadata.create_all(bind=connection)
    config.attributes["connection"] = connection
    command.stamp(config, "heads")

    verification = MigrationContext.configure(connection)
    final_heads = tuple(sorted(verification.get_current_heads()))
    if final_heads != target:
        raise MigrationGateError(
            "Fresh DairyOS database bootstrap did not reach all expected heads. "
            f"Expected {target}; found {final_heads}."
        )


def migrate_if_needed() -> MigrationResult:
    """Safely prepare a DairyOS database for production startup.

    A PostgreSQL transaction-level advisory lock serializes migration checks
    across processes. The same SQLAlchemy connection is handed to Alembic so
    the lock remains active for the actual migration transaction.

    A genuinely empty database is initialized once from the current canonical
    ORM schema and immediately stamped at the packaged Alembic head. This is
    deliberately restricted to databases with no application tables.

    A non-empty database without Alembic history is still refused: DairyOS will
    never guess whether an unknown schema is complete enough to upgrade safely.
    Existing databases that already have migration history continue through the
    normal Alembic migration chain, with a verified pre-migration backup.
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

            application_tables = _public_application_table_count(connection)

            if not current and application_tables == 0:
                try:
                    inspect_startup_integrity(application_tables=0)
                except StartupIntegrityError as exc:
                    raise MigrationGateError(str(exc)) from exc
                _bootstrap_empty_database(connection, config, target)
                return MigrationResult(True, current, target, None)

            if not current:
                raise MigrationGateError(
                    "DairyOS database has application tables but no Alembic history. "
                    "Startup is blocked because the existing schema cannot be safely inferred."
                )

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
