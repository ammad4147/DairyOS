"""Safe startup migration gate for the packaged DairyOS runtime."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from dairyos.data.database.destructive_guards import (
    install_destructive_guards,
    verify_destructive_guards,
)
from dairyos.data.database.restore_verification import (
    restore_verification_due,
    verify_latest_backup_restore,
)
from dairyos.lifecycle.manager import LifecycleManager
from dairyos.platform import paths
from dairyos.windows.startup_integrity import (
    StartupIntegrityError,
    inspect_startup_integrity,
)


MIGRATION_LOCK_KEY = 746182934517
MIGRATION_DATABASE_URL_ENV = "DAIRYOS_MIGRATION_DATABASE_URL"
LOG = logging.getLogger(__name__)


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
    """Resolve the privileged migration URL when the packaged supervisor supplied one."""
    privileged = os.environ.get(MIGRATION_DATABASE_URL_ENV, "").strip()
    if privileged:
        return privileged

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
    """Create and protect the current ORM schema for a genuinely empty database.

    The fresh-install path intentionally uses the current canonical ORM schema
    rather than replaying years of historical migrations.  Because it stamps
    directly at Alembic heads, database security primitives that would normally
    arrive through migrations must be installed explicitly before the stamp.
    """
    from dairyos.data.database.base import Base
    import dairyos.data.database.database  # noqa: F401  # registers all ORM models

    Base.metadata.create_all(bind=connection)
    install_destructive_guards(connection)
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

    A packaged private installation supplies a separate administrator URL only
    for this gate.  The URL is consumed here and removed from the environment in
    ``finally`` before the normal backend child is started.

    When a verified scheduled backup exists, this same short-lived privileged
    boundary also performs the weekly scratch-restore proof.  A failed recovery
    proof is persisted into backup health and logged prominently, while normal
    farm startup remains available so a backup subsystem fault does not itself
    stop farm operations.
    """
    transient_admin_url = os.environ.get(MIGRATION_DATABASE_URL_ENV, "").strip()
    engine = None
    backup_path: Path | None = None

    try:
        database_url = _database_url()
        config, script = _build_config()
        engine = create_engine(database_url, pool_pre_ping=True)

        with engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(:lock_key)"),
                {"lock_key": MIGRATION_LOCK_KEY},
            )
            migration_context = MigrationContext.configure(connection)
            current = tuple(sorted(migration_context.get_current_heads()))
            target = tuple(sorted(script.get_heads()))
            application_tables = _public_application_table_count(connection)

            if application_tables == 0:
                try:
                    inspect_startup_integrity(application_tables=0)
                except StartupIntegrityError as exc:
                    raise MigrationGateError(str(exc)) from exc

                if current == target:
                    raise MigrationGateError(
                        "DairyOS database reports the packaged migration head but contains no "
                        "application tables. Startup is blocked because farm data may have been "
                        "removed or the database is otherwise inconsistent. Data recovery is required."
                    )

                if not current:
                    _bootstrap_empty_database(connection, config, target)
                    return MigrationResult(True, current, target, None)

            if current == target:
                if transient_admin_url:
                    install_destructive_guards(connection)
                else:
                    verify_destructive_guards(connection)
                return MigrationResult(False, current, target)

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
                install_destructive_guards(connection)
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
        if engine is not None:
            engine.dispose()
        if transient_admin_url:
            try:
                if restore_verification_due():
                    result = verify_latest_backup_restore(transient_admin_url)
                    if result is not None:
                        LOG.info("DairyOS weekly backup restore verification passed: %s", result)
            except Exception:
                LOG.exception(
                    "DairyOS weekly backup restore verification FAILED. "
                    "Farm startup will continue, but Data Protection is degraded until recovery verification succeeds."
                )
            finally:
                os.environ.pop(MIGRATION_DATABASE_URL_ENV, None)
