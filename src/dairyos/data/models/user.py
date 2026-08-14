from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class User(Base):
    """A real, persisted farm-account (D3, 2026-08-14).

    Before this model existed, DairyOS had exactly one authenticatable
    identity: a single env-var-configured admin login
    (``DAIRYOS_ADMIN_USERNAME``/``DAIRYOS_ADMIN_PASSWORD``/
    ``DAIRYOS_ADMIN_ROLE``), handled entirely in ``dairyos.api.auth``. Five
    separate "identity"/RBAC trees (``application/identity``,
    ``core/identity``, ``core/models/{user,role}.py``, ``operations/users``,
    ``platform/identity``) existed alongside it, fully wired into
    ``ApplicationRuntime``/``RuntimeContainer``, but had zero live callers
    anywhere in ``api/`` -- dead weight, not a working multi-user system.
    Decision D3 (2026-08-13): delete all five and build one minimal model
    instead, additive to (not replacing) the existing env-var admin path.

    Passwords are hashed with salted PBKDF2-HMAC-SHA256 (200k iterations),
    not the existing ``core.security.password.hash_password`` (plain
    unsalted SHA-256) -- that function is itself dead code, out of D3's
    deletion list, and too weak to build new accounts on.

    ``role`` is governed: see ``GOVERNED["auth_roles"]`` in
    ``dairyos.api.reference_data`` for the authoritative OWNER/MANAGER/
    MILKER vocabulary. This table intentionally has no ``permissions``
    column or join table -- D3 asked for the minimal model that fits the
    existing bearer-token layer, not the deleted fine-grained permission
    system.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=False)
    role = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
