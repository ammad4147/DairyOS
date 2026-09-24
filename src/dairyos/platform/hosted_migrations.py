"""Platform-neutral schema gate for the hosted DairyOS runtime."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from dairyos.data.database.destructive_guards import (
    install_destructive_guards,
    verify_destructive_guards,
)
from dairyos.lifecycle.manager import LifecycleManager
from dairyos.platform import paths
from dairyos.platform.postgres_environment import isolated_postgres_environment

MIGRATION_LOCK_KEY = 746182934517
EMPTY_DATABASE_CONFIRM_ENV = "DAIRYOS_HOSTED_BOOTSTRAP_DATABASE"


class HostedMigrationError(RuntimeError):
    """Raised when a hosted database cannot safely reach the current schema."""


@dataclass(frozen=True)
class HostedMigrationResult:
    migrated: bool
    current_heads: tuple[str, ...]
    target_heads: tuple[str, ...]
    backup_path: Path | None = None


def _find_alembic_ini() -> Path:
    candidates: list[Path] = []
    override = os.environ.get("DAIRYOS_ALEMBIC_INI", "").strip()
    if override:
        candidates.append(Path(override).expanduser())
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "alembic.ini")
    candidates.extend((Path.cwd() / "alembic.ini", Path(__file__).resolve().parents[3] / "alembic.ini"))
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate.is_file():
            return candidate
    raise HostedMigrationError("DairyOS Alembic configuration was not found.")


def _build_alembic_config() -> tuple[Config, ScriptDirectory]:
    ini = _find_alembic_ini()
    config = Config(str(ini))
    script_location = Path(config.get_main_option("script_location"))
    if not script_location.is_absolute():
        script_location = (ini.parent / script_location).resolve()
    if not script_location.is_dir():
        raise HostedMigrationError(f"DairyOS migration scripts are missing: {script_location}")
    config.set_main_option("script_location", str(script_location))
    return config, ScriptDirectory.from_config(config)


def _database_url(database_url: str | None) -> str:
    value = (database_url or os.environ.get("DAIRYOS_DATABASE_URL", "")).strip()
    if not value:
        raise HostedMigrationError("DAIRYOS_DATABASE_URL is required for hosted startup.")
    try:
        parsed = make_url(value)
    except Exception as exc:
        raise HostedMigrationError("DAIRYOS_DATABASE_URL is invalid.") from exc
    if parsed.get_backend_name() != "postgresql":
        raise HostedMigrationError("Hosted DairyOS requires PostgreSQL.")
    if not parsed.database or not parsed.username:
        raise HostedMigrationError("Hosted PostgreSQL URL must name a database and role.")
    if parsed.host not in {"localhost", "127.0.0.1", "::1"} and not parsed.password:
        raise HostedMigrationError(
            "Hosted PostgreSQL connections outside loopback require credentials."
        )
    return value


def _application_table_count(connection) -> int:
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


def _bootstrap_empty_database(
    connection,
    config: Config,
    target_heads: tuple[str, ...],
    database_name: str,
) -> None:
    confirmation = os.environ.get(EMPTY_DATABASE_CONFIRM_ENV, "").strip()
    if confirmation != database_name:
        raise HostedMigrationError(
            "Hosted database is empty. To initialize this exact database, set "
            f"{EMPTY_DATABASE_CONFIRM_ENV} to its database name ({database_name})."
        )

    # Bootstrap only a genuinely empty database after explicit operator intent.
    import dairyos.data.database.database  # noqa: F401
    from dairyos.data.database.base import Base

    Base.metadata.create_all(bind=connection)
    install_destructive_guards(connection)
    config.attributes["connection"] = connection
    command.stamp(config, "heads")
    final_heads = tuple(sorted(MigrationContext.configure(connection).get_current_heads()))
    if final_heads != target_heads:
        raise HostedMigrationError(
            "Hosted empty-database bootstrap did not reach all migration heads. "
            f"Expected {target_heads}; found {final_heads}."
        )


def migrate_hosted_database(
    database_url: str | None = None,
) -> HostedMigrationResult:
    """Safely verify or migrate a hosted PostgreSQL database before API startup.

    Existing unversioned application schemas are never guessed or altered. An
    empty database requires explicit confirmation naming that database. Schema
    upgrades are serialized and require a verified pre-migration backup.
    """
    resolved_url = _database_url(database_url)
    parsed_url = make_url(resolved_url)
    engine = None
    try:
        config, script = _build_alembic_config()
        engine = create_engine(resolved_url, pool_pre_ping=True)
        with isolated_postgres_environment(), engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(:lock_key)"),
                {"lock_key": MIGRATION_LOCK_KEY},
            )
            migration_context = MigrationContext.configure(connection)
            current_heads = tuple(sorted(migration_context.get_current_heads()))
            target_heads = tuple(sorted(script.get_heads()))
            application_tables = _application_table_count(connection)

            if application_tables == 0:
                if current_heads == target_heads:
                    raise HostedMigrationError(
                        "Hosted database reports current migration heads but has no "
                        "application tables; startup is blocked pending recovery."
                    )
                _bootstrap_empty_database(
                    connection,
                    config,
                    target_heads,
                    str(parsed_url.database),
                )
                return HostedMigrationResult(True, current_heads, target_heads)

            if current_heads == target_heads:
                verify_destructive_guards(connection)
                return HostedMigrationResult(False, current_heads, target_heads)

            if not current_heads:
                raise HostedMigrationError(
                    "Hosted database has application tables but no Alembic history. "
                    "Startup is blocked; the existing schema cannot be inferred safely."
                )

            manager = LifecycleManager(
                installation_root=os.environ.get(
                    "DAIRYOS_INSTALL_ROOT", str(Path.cwd())
                ),
                data_root=paths.data_root(create=True),
                database_url=resolved_url,
            )
            try:
                backup_path = manager.backup(
                    label="pre-migration",
                    require_database=True,
                )
                from dairyos.lifecycle.backup_validation import verified_manifest

                backup_manifest = verified_manifest(backup_path)
                if (
                    backup_manifest.get("database_backup_archive_verified") is not True
                    or not backup_manifest.get("database_backup")
                ):
                    raise HostedMigrationError(
                        "Hosted pre-migration backup was not recorded as a verified "
                        "database archive; startup is blocked."
                    )
            except Exception as exc:
                raise HostedMigrationError(
                    f"Hosted pre-migration backup failed; startup is blocked: {exc}"
                ) from exc

            config.attributes["connection"] = connection
            try:
                command.upgrade(config, "heads")
                install_destructive_guards(connection)
            except Exception as exc:
                raise HostedMigrationError(
                    "Hosted database migration failed. Startup is blocked. "
                    f"Pre-migration backup: {backup_path}. Original error: {exc}"
                ) from exc

            final_heads = tuple(
                sorted(MigrationContext.configure(connection).get_current_heads())
            )
            if final_heads != target_heads:
                raise HostedMigrationError(
                    "Hosted migration completed without reaching all expected heads. "
                    f"Expected {target_heads}; found {final_heads}. "
                    f"Pre-migration backup: {backup_path}"
                )
            return HostedMigrationResult(
                True,
                current_heads,
                target_heads,
                backup_path,
            )
    except HostedMigrationError:
        raise
    except Exception as exc:
        raise HostedMigrationError(
            f"Hosted database preflight failed; startup is blocked: {exc}"
        ) from exc
    finally:
        if engine is not None:
            engine.dispose()
