"""Farm settings service (AA-013 §17 Settings, 2026-08-14).

Backs two concrete, currently-shipped settings while the full
roles/preferences Settings section (AA-013 §17) is still pending:

- Farm identity (``farm_name``, ``animal_id_prefix``) -- the short,
  farm-branded Animal ID scheme. Default is "Trident Dairies" / "TD",
  matching this farm, but both are editable so the same code works for
  any farm and survives a rename.
- Reset protection (``reset_protected``, ``reset_password_hash``) --
  gates ``POST /settings/reset-test-data``. Off by default (this farm is
  still in build-out, per the 2026-08-14 decision); an operator turns it
  on, once, from Settings before going live.

Password hashing mirrors ``dairyos.api.auth``'s salted PBKDF2-HMAC-SHA256
scheme (200k iterations) rather than importing it directly -- that
function lives in the API layer, and a farm settings service reaching
into an API module would invert the dependency direction the rest of
this codebase uses (services are called by API routers, never the other
way around).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

DEFAULT_FARM_NAME = "Trident Dairies"
DEFAULT_ANIMAL_ID_PREFIX = "TD"
_PBKDF2_ITERATIONS = 200_000


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
    )
    return f"{salt}${derived.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except (ValueError, AttributeError):
        return False
    candidate = _hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, stored)


class FarmSettingsService:
    def __init__(self, repository):
        self.repository = repository

    # -- Farm identity ----------------------------------------------------

    def get_public_settings(self) -> dict:
        return {
            "farm_name": self.repository.get("farm_name", DEFAULT_FARM_NAME),
            "animal_id_prefix": self.get_animal_id_prefix(),
            "reset_protected": self.is_reset_protected(),
        }

    def get_animal_id_prefix(self) -> str:
        prefix = self.repository.get("animal_id_prefix", DEFAULT_ANIMAL_ID_PREFIX)
        prefix = (prefix or "").strip().upper()
        return prefix or DEFAULT_ANIMAL_ID_PREFIX

    def update_identity(self, *, farm_name: str | None = None, animal_id_prefix: str | None = None,
                         updated_by: str | None = None) -> dict:
        if farm_name is not None:
            farm_name = farm_name.strip()
            if not farm_name:
                raise ValueError("farm_name cannot be blank")
            self.repository.set("farm_name", farm_name, updated_by=updated_by)

        if animal_id_prefix is not None:
            prefix = animal_id_prefix.strip().upper()
            if not (1 <= len(prefix) <= 6) or not prefix.isalpha():
                raise ValueError("animal_id_prefix must be 1-6 letters (e.g. \"TD\")")
            self.repository.set("animal_id_prefix", prefix, updated_by=updated_by)

        return self.get_public_settings()

    # -- Reset protection ---------------------------------------------------

    def is_reset_protected(self) -> bool:
        return self.repository.get("reset_protected", "false") == "true"

    def set_reset_protection(self, *, enabled: bool, password: str | None = None,
                              updated_by: str | None = None) -> dict:
        if enabled:
            if not password or len(password) < 4:
                raise ValueError("A password of at least 4 characters is required to enable reset protection")
            self.repository.set("reset_password_hash", _hash_password(password), updated_by=updated_by)
        self.repository.set("reset_protected", "true" if enabled else "false", updated_by=updated_by)
        return self.get_public_settings()

    def verify_reset_password(self, password: str | None) -> bool:
        stored = self.repository.get("reset_password_hash")
        if not stored or not password:
            return False
        return _verify_password(password, stored)
