"""Credential lifecycle for the standalone DairyOS Admin Tool."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import tempfile
import time

from dairyos.platform import paths

AUTH_VERSION = 1
AUTH_FILENAME = "admin-auth.json"
AUDIT_FILENAME = "admin-audit.jsonl"
PBKDF2_ITERATIONS = 600_000
MIN_PASSWORD_LENGTH = 12
RECOVERY_BYTES = 18


class AdminAuthenticationError(RuntimeError):
    """Raised when Admin Tool authentication or recovery fails."""


def auth_state_path() -> Path:
    return paths.data_root(create=True) / "security" / AUTH_FILENAME


def audit_path() -> Path:
    return paths.data_root(create=True) / "security" / AUDIT_FILENAME


def configured() -> bool:
    return auth_state_path().is_file()


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _derive(value: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        value.encode("utf-8"),
        salt,
        iterations,
        dklen=32,
    )


def _verifier(value: str) -> dict[str, object]:
    salt = secrets.token_bytes(16)
    digest = _derive(value, salt)
    return {
        "algorithm": "pbkdf2-sha256",
        "iterations": PBKDF2_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "digest": base64.b64encode(digest).decode("ascii"),
    }


def _matches(value: str, payload: dict[str, object]) -> bool:
    try:
        if payload.get("algorithm") != "pbkdf2-sha256":
            return False
        iterations = int(payload["iterations"])
        salt = base64.b64decode(str(payload["salt"]))
        expected = base64.b64decode(str(payload["digest"]))
    except Exception:
        return False
    actual = _derive(value, salt, iterations)
    return hmac.compare_digest(actual, expected)


def _read_state() -> dict[str, object]:
    path = auth_state_path()
    if not path.is_file():
        raise AdminAuthenticationError(
            "DairyOS Admin Tool password has not been configured."
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdminAuthenticationError(
            "DairyOS Admin Tool credential state is unreadable."
        ) from exc
    if not isinstance(payload, dict) or payload.get("version") != AUTH_VERSION:
        raise AdminAuthenticationError(
            "DairyOS Admin Tool credential state is unsupported or invalid."
        )
    return payload


def _validate_password_policy(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AdminAuthenticationError(
            f"Administrator password must contain at least {MIN_PASSWORD_LENGTH} characters."
        )
    if password.strip() != password:
        raise AdminAuthenticationError(
            "Administrator password cannot begin or end with spaces."
        )


def _new_recovery_key() -> str:
    raw = base64.b32encode(secrets.token_bytes(RECOVERY_BYTES)).decode("ascii").rstrip("=")
    groups = [raw[i : i + 5] for i in range(0, len(raw), 5)]
    return "-".join(groups)


def record_audit(event: str, *, success: bool, detail: str = "") -> None:
    path = audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": time.time(),
        "event": event,
        "success": bool(success),
        "detail": detail[:1000],
    }
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def read_audit(limit: int = 100) -> list[dict[str, object]]:
    path = audit_path()
    if not path.is_file():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows[-max(1, limit) :]


def setup(password: str, confirmation: str) -> str:
    if configured():
        raise AdminAuthenticationError(
            "DairyOS Admin Tool password is already configured."
        )
    if password != confirmation:
        raise AdminAuthenticationError("Administrator password confirmation does not match.")
    _validate_password_policy(password)
    recovery_key = _new_recovery_key()
    _atomic_json(
        auth_state_path(),
        {
            "version": AUTH_VERSION,
            "password": _verifier(password),
            "recovery": _verifier(recovery_key),
            "failed_attempts": 0,
        },
    )
    record_audit("admin-password-setup", success=True)
    return recovery_key


def verify_password(password: str, *, audit: bool = True) -> bool:
    state = _read_state()
    ok = _matches(password, dict(state.get("password") or {}))
    state["failed_attempts"] = 0 if ok else int(state.get("failed_attempts", 0)) + 1
    _atomic_json(auth_state_path(), state)
    if audit:
        record_audit("admin-login", success=ok)
    if not ok:
        failures = int(state["failed_attempts"])
        time.sleep(min(2.0, 0.20 * failures))
    return ok


def require_password(password: str, *, event: str = "admin-reauth") -> None:
    if not verify_password(password, audit=False):
        record_audit(event, success=False)
        raise AdminAuthenticationError("Administrator password is incorrect.")
    record_audit(event, success=True)


def change_password(current: str, new_password: str, confirmation: str) -> str:
    require_password(current, event="admin-password-change-auth")
    if new_password != confirmation:
        raise AdminAuthenticationError("New password confirmation does not match.")
    _validate_password_policy(new_password)
    state = _read_state()
    recovery_key = _new_recovery_key()
    state["password"] = _verifier(new_password)
    state["recovery"] = _verifier(recovery_key)
    state["failed_attempts"] = 0
    _atomic_json(auth_state_path(), state)
    record_audit("admin-password-changed", success=True)
    return recovery_key


def recover_password(
    recovery_key: str,
    new_password: str,
    confirmation: str,
) -> str:
    state = _read_state()
    if not _matches(recovery_key.strip().upper(), dict(state.get("recovery") or {})):
        record_audit("admin-password-recovery", success=False)
        raise AdminAuthenticationError("Recovery key is invalid.")
    if new_password != confirmation:
        raise AdminAuthenticationError("New password confirmation does not match.")
    _validate_password_policy(new_password)
    next_key = _new_recovery_key()
    state["password"] = _verifier(new_password)
    state["recovery"] = _verifier(next_key)
    state["failed_attempts"] = 0
    _atomic_json(auth_state_path(), state)
    record_audit("admin-password-recovery", success=True)
    return next_key
