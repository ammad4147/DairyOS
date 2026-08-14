"""Application settings (AA-013 §17 Settings section; farm identity and
reset protection, 2026-08-14).

A small key/value store for the handful of operator-configurable settings
DairyOS needs before the full roles/preferences Settings section (AA-013
§17) is built. Key/value rather than dedicated columns means later
settings (added as the Settings section grows) don't each need their own
migration.

Two concrete uses exist today:

- ``farm_name`` / ``animal_id_prefix`` -- the short, farm-branded Animal ID
  scheme (e.g. "Trident Dairies" -> prefix "TD" -> animal IDs "TD-001",
  "TD-002", ...), replacing the previous 32-character random hex ID.
- ``reset_protected`` / ``reset_password_hash`` -- gates
  ``POST /settings/reset-test-data``. Unprotected by default (pre-
  deployment convenience); the operator can turn on password protection
  once from Settings before going live, per the decision recorded
  2026-08-14.
"""

from sqlalchemy import Column, DateTime, String

from dairyos.core.time_utils import utcnow
from dairyos.data.database.base import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    updated_by = Column(String, nullable=True)
