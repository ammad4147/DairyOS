"""Durable farm identity for data portability and recovery.

Every DairyOS farm has a persistent ``farm_instance_id`` (UUIDv4) that
survives export, import, backup, and restoration.  This identity is distinct
from deployment metadata (installation path, data root, machine hostname)
which is re-generated on each installation.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from dairyos.core.time_utils import utcnow

LOG = logging.getLogger(__name__)

FARM_INSTANCE_ID_KEY = "farm_instance_id"


def get_or_create_farm_instance_id(session: Session) -> str:
    """Return the durable farm identity, initializing it if absent.

    The farm_instance_id is stored in the ``app_settings`` table.  On a
    genuinely new installation, a fresh UUIDv4 is generated and persisted.
    On import, the imported identity replaces the local one.
    """
    result = session.execute(
        text("SELECT value FROM app_settings WHERE key = :key"),
        {"key": FARM_INSTANCE_ID_KEY},
    ).scalar_one_or_none()

    if result:
        return str(result)

    farm_id = str(uuid.uuid4())
    updated_at = utcnow()
    session.execute(
        text(
            "INSERT INTO app_settings (key, value, updated_at) "
            "VALUES (:key, :value, :updated_at) "
            "ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = :updated_at"
        ),
        {"key": FARM_INSTANCE_ID_KEY, "value": farm_id, "updated_at": updated_at},
    )
    session.commit()
    LOG.info("DairyOS farm identity initialized: %s", farm_id)
    return farm_id


def set_farm_instance_id(session: Session, farm_id: str) -> None:
    """Replace the farm identity (used during import to preserve the source farm's ID)."""
    updated_at = utcnow()
    session.execute(
        text(
            "INSERT INTO app_settings (key, value, updated_at) "
            "VALUES (:key, :value, :updated_at) "
            "ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = :updated_at"
        ),
        {"key": FARM_INSTANCE_ID_KEY, "value": farm_id, "updated_at": updated_at},
    )
    session.commit()
    LOG.info("DairyOS farm identity set to: %s", farm_id)


def read_farm_instance_id(session: Session) -> str | None:
    """Return the farm identity or None if not yet initialized."""
    result = session.execute(
        text("SELECT value FROM app_settings WHERE key = :key"),
        {"key": FARM_INSTANCE_ID_KEY},
    ).scalar_one_or_none()
    return str(result) if result else None
