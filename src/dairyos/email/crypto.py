from __future__ import annotations

import base64
import hashlib
import json
import os

from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    secret = os.getenv("DAIRYOS_EMAIL_SECRET") or os.getenv("DAIRYOS_AUTH_SECRET")
    if not secret:
        raise RuntimeError(
            "DAIRYOS_EMAIL_SECRET or DAIRYOS_AUTH_SECRET must be configured to store SMTP credentials"
        )
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if os.name == "nt":
        from dairyos.windows.protected_secret import protect_bytes

        return json.dumps(
            {
                "version": 1,
                "scheme": "windows-dpapi-user",
                "value": base64.b64encode(protect_bytes(value.encode("utf-8"))).decode(
                    "ascii"
                ),
            },
            sort_keys=True,
        )
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    if value.lstrip().startswith("{"):
        from dairyos.windows.protected_secret import unprotect_bytes

        try:
            envelope = json.loads(value)
            if (
                envelope.get("version") != 1
                or envelope.get("scheme") != "windows-dpapi-user"
                or os.name != "nt"
            ):
                raise ValueError("Unsupported protected credential envelope")
            return unprotect_bytes(
                base64.b64decode(envelope["value"], validate=True)
            ).decode("utf-8")
        except (ValueError, TypeError, KeyError, OSError) as exc:
            raise RuntimeError(
                "SMTP credential cannot be unlocked; replace it under the intended Windows operator account."
            ) from exc
    # Existing Fernet ciphertext remains readable with its original deployment
    # secret. A subsequent password replacement writes the Windows envelope.
    return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
