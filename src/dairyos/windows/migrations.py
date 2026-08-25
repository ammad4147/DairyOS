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
    try:
        from dairyos.data.database.session import DATABASE_URL
    except Exception as exc:
        raise MigrationGateError(f"Unable to resolve the DairyOS database configuration: {exc}") from exc
    if not DATABASE_URL:
        raise MigrationGateError("DairyOS database configuration is empty.")
    return DATABASE_URL


def migrate_if_needed() -> MigrationResult:
    """Backup and migrate only when the database is behind the packaged head.

    A PostgreSQL transaction-level advisory lock serializes migration checks
    across processes. The same SQLAlchemy connection is handed to Alembic so
    the lock remains active for the actual migration transaction. A verified
    pre-migration backup is created before any schema change. Migration
    failures are propagated without an automatic restore; the backup remains
    available for controlled recovery.
    """
    database_url = _database_url()
    config, script = _build_config()
    engine = create_engine(database_url, pool_pre_ping=True)
    backup_path: Path | None = None

    try:
        with engine.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": MIGRATION_LOCK_KEY})
            migration_context = MigrationContext.configure(connection)
            current = tuple(sorted(migration_context.get_current_heads()))
            target = tuple(sorted(script.get_heads()))

            if current == target:
                return MigrationResult(False, current, target)

            manager = LifecycleManager(
                installation_root=Path(sys.executable).resolve().parent,
                data_root=paths.data_root(create=True),
                database_url=database_url,
            )
            try:
                backup_path = manager.backup(label="pre-migration")
            except Exception as exc:
                raise MigrationGateError(f"Pre-migration backup failed; startup is blocked: {exc}") from exc

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
        raise MigrationGateError(f"DairyOS database preflight failed; startup is blocked: {exc}") from exc
    finally:
        engine.dispose()
