"""Operational authentication and role identity for DairyOS.

This module keeps the existing ``/login`` contract while providing signed,
self-contained bearer tokens. Farm write routes may continue to operate in
local/operator mode without a token so the existing operator UI contract is
not broken; when a bearer token is supplied, its authenticated identity is the
only authoritative operator attribution. Invalid bearer tokens are rejected
and never fall back to a client-supplied operator value.

Identity model (D3, 2026-08-14): before this, DairyOS had exactly one
authenticatable identity -- a single env-var-configured admin login -- and,
separately, five dead "identity"/RBAC trees wired into the application
runtime with zero live callers anywhere in ``api/``. Those five trees were
deleted rather than kept as unreachable code. In their place this module
now checks a real, persisted multi-user table
(``dairyos.data.models.user.User``) FIRST, by username; if no matching row
exists it falls back UNCHANGED to the original single env-var admin check
below (``_configured_username``/``_configured_password``/
``_configured_role``). This is deliberately additive, not a replacement --
every pre-existing test asserting the legacy env-var admin login's exact
behaviour (including an arbitrary, non-governed role string via
``DAIRYOS_ADMIN_ROLE``) continues to pass unchanged.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from dairyos.api.reference_data import GOVERNED
from dairyos.data.repositories.repository_factory import RepositoryFactory

router = APIRouter(tags=["Authentication"])

_bearer = HTTPBearer(auto_error=False)

_PBKDF2_ITERATIONS = 200_000


class LoginRequest(BaseModel):
    """Credentials accepted by the operator login endpoint."""

    username: str = Field(default="admin", min_length=1)
    password: str = Field(default="dairyos", min_length=1)


class CreateUserRequest(BaseModel):
    """Payload for creating a new persisted farm account (OWNER-only)."""

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    role: str = Field(min_length=1)


def _configured_username() -> str:
    return os.getenv("DAIRYOS_ADMIN_USERNAME", "admin")


def _configured_password() -> str:
    return os.getenv("DAIRYOS_ADMIN_PASSWORD", "dairyos")


def _configured_role() -> str:
    return os.getenv("DAIRYOS_ADMIN_ROLE", "OWNER")


def _signing_secret() -> bytes:
    secret = os.getenv("DAIRYOS_AUTH_SECRET")
    if not secret:
        env = os.getenv("DAIRYOS_ENV", "development").lower()
        if env in ("production", "staging", "test", "preprod"):
            raise RuntimeError(f"DAIRYOS_AUTH_SECRET must be explicitly configured in environment '{env}'")
        secret = "dairyos-development-secret-unsafe-fallback"
    return secret.encode("utf-8")


def _encode_token(claims: dict[str, Any]) -> str:
    payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).rstrip(b"=")
    signature = hmac.new(_signing_secret(), encoded, hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=")
    return f"{encoded.decode('ascii')}.{encoded_signature.decode('ascii')}"


def _decode_token(token: str) -> dict[str, Any]:
    try:
        encoded, encoded_signature = token.split(".", 1)
        supplied_signature = base64.urlsafe_b64decode(encoded_signature + "===")
        expected_signature = hmac.new(
            _signing_secret(), encoded.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ValueError("invalid signature")

        payload = base64.urlsafe_b64decode(encoded + "===")
        claims = json.loads(payload.decode("utf-8"))
        if not isinstance(claims, dict):
            raise ValueError("invalid claims")

        if int(claims.get("exp", 0)) < int(time.time()):
            raise ValueError("expired token")

        if not claims.get("sub") or not claims.get("role"):
            raise ValueError("missing identity claims")

        return claims
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


# ---------------------------------------------------------------------------
# Password hashing for the new persisted User table (salted PBKDF2). This is
# deliberately NOT dairyos.core.security.password.hash_password (plain
# unsalted SHA-256) -- that module is itself dead code, out of D3's deletion
# list, and too weak to build new accounts on.
# ---------------------------------------------------------------------------


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
    )
    return derived.hex(), salt


def _verify_password(password: str, password_hash: str, salt: str) -> bool:
    candidate, _ = _hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, password_hash)


def _find_persisted_user(username: str):
    factory = RepositoryFactory.create()
    try:
        return factory.users().get_by_username(username)
    finally:
        factory.close()


@router.post("/login")
def login(credentials: LoginRequest | None = None):
    """Authenticate a farm account and issue a bearer token.

    Checks the persisted user table first, by username. If no row matches,
    falls back unchanged to the legacy single env-var-configured admin
    login for backward compatibility.
    """

    supplied = credentials or LoginRequest()

    persisted_user = _find_persisted_user(supplied.username)
    if persisted_user is not None:
        if not persisted_user.active or not _verify_password(
            supplied.password, persisted_user.password_hash, persisted_user.password_salt
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        role = persisted_user.role
    else:
        expected_username = _configured_username()
        expected_password = _configured_password()

        if not hmac.compare_digest(
            supplied.username, expected_username
        ) or not hmac.compare_digest(supplied.password, expected_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        role = _configured_role()

    now = int(time.time())
    claims = {
        "sub": supplied.username,
        "role": role,
        "iat": now,
        "exp": now + int(os.getenv("DAIRYOS_AUTH_TOKEN_TTL", "28800")),
    }

    return {
        "access_token": _encode_token(claims),
        "token_type": "bearer",
        "user": {"username": supplied.username, "role": claims["role"]},
        "expires_at": claims["exp"],
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    """Return the authenticated operator identity for protected routes."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _decode_token(credentials.credentials)


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any] | None:
    """Return authenticated identity when supplied; preserve anonymous UI writes.

    If a bearer token is supplied it must be valid. An authenticated ``sub`` is
    then authoritative for operator attribution. With no token, existing farm
    write routes remain usable and retain their explicit operator field for
    backwards-compatible local/operator workflows.
    """

    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode_token(credentials.credentials)


def require_role(*allowed_roles: str):
    """FastAPI dependency factory: authenticated identity restricted to specific roles."""

    def _dependency(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this action",
            )
        return user

    return _dependency


@router.get("/me")
def current_user(user: dict[str, Any] = Depends(get_current_user)):
    """Return the authenticated operator identity and role."""

    return {
        "username": user["sub"],
        "role": user["role"],
        "issued_at": user["iat"],
        "expires_at": user["exp"],
    }


@router.post("/users")
def create_user(
    payload: CreateUserRequest,
    _owner: dict[str, Any] = Depends(require_role("OWNER")),
):
    """Create a new persisted farm account. OWNER role required."""

    if payload.role not in GOVERNED["auth_roles"]:
        raise HTTPException(
            status_code=422,
            detail=f"role must be one of {GOVERNED['auth_roles']}",
        )

    factory = RepositoryFactory.create()
    try:
        users = factory.users()
        if users.exists_username(payload.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this username already exists",
            )

        from dairyos.data.models.user import User

        password_hash, salt = _hash_password(payload.password)
        created = users.add(
            User(
                username=payload.username,
                password_hash=password_hash,
                password_salt=salt,
                role=payload.role,
                active=True,
            )
        )
        return {
            "id": created.id,
            "username": created.username,
            "role": created.role,
            "active": created.active,
        }
    finally:
        factory.close()


@router.get("/users")
def list_users(_owner: dict[str, Any] = Depends(require_role("OWNER"))):
    """List persisted farm accounts. OWNER role required."""

    factory = RepositoryFactory.create()
    try:
        return {
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "role": u.role,
                    "active": u.active,
                }
                for u in factory.users().get_all()
            ]
        }
    finally:
        factory.close()

