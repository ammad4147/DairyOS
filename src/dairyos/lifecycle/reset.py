"""Canonical, transactional DairyOS operational-data reset boundary."""

from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from dairyos.farm.settings.services.deployment_control_service import DeploymentControlService
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService
from dairyos.data.repositories.app_setting_repository import AppSettingRepository
from dairyos.lifecycle.manager import LifecycleError


PRESERVED_TABLES = frozenset(
    {
        "alembic_version",
        "app_settings",
        "users",
        "drug_withdrawal_reference",
        "email_sender_settings",
    }
)


@dataclass(frozen=True)
class ResetExecution:
    tables_cleared: tuple[str, ...]


def reset_operational_data(database_url: str, *, updated_by: str) -> ResetExecution:
    """Atomically deactivate deployment and clear all non-preserved tables.

    This is deliberately a lifecycle primitive rather than an application API.
    The caller is responsible for creating and verifying the external recovery
    snapshot before invoking this function.
    """
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        tables = tuple(
            sorted(table for table in inspector.get_table_names() if table not in PRESERVED_TABLES)
        )
        with Session(engine) as session:
            with session.begin():
                deployment = DeploymentControlService(
                    FarmSettingsService(AppSettingRepository(session=session, commit=False))
                )
                deployment.deactivate(updated_by=updated_by)
                if tables:
                    quoted = ", ".join('"' + table.replace('"', '""') + '"' for table in tables)
                    session.execute(
                        sa.text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
                    )
        remaining = verify_zero_state(database_url)
        if remaining:
            raise LifecycleError(
                "Reset zero-state verification failed: "
                + ", ".join(f"{table}={count}" for table, count in sorted(remaining.items()))
            )
        return ResetExecution(tables_cleared=tables)
    finally:
        engine.dispose()


def verify_zero_state(database_url: str) -> dict[str, int]:
    """Return non-preserved tables that still contain rows."""
    engine = create_engine(database_url)
    try:
        remaining: dict[str, int] = {}
        inspector = inspect(engine)
        with engine.connect() as connection:
            for table in inspector.get_table_names():
                if table in PRESERVED_TABLES:
                    continue
                quoted = '"' + table.replace('"', '""') + '"'
                count = int(
                    connection.execute(sa.text(f"SELECT count(*) FROM {quoted}")).scalar_one()
                )
                if count:
                    remaining[table] = count
        return remaining
    finally:
        engine.dispose()
