from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    secret = os.getenv("DAIRYOS_EMAIL_SECRET") or os.getenv("DAIRYOS_AUTH_SECRET")
    if not secret:
        raise RuntimeError("DAIRYOS_EMAIL_SECRET or DAIRYOS_AUTH_SECRET must be configured to store SMTP credentials")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
