"""Operational authentication and role identity for DairyOS.

This module intentionally keeps the existing ``/login`` contract while replacing
its static token with a signed, self-contained bearer token. Credentials and the
signing secret are environment-configurable so the same API can be used locally
and in a deployed farm environment without introducing a second user store.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

router = APIRouter(tags=["Authentication"])

_bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    """Credentials accepted by the operator login endpoint."""

    username: str = Field(default="admin", min_length=1)
    password: str = Field(default="dairyos", min_length=1)


def _configured_username() -> str:
    return os.getenv("DAIRYOS_ADMIN_USERNAME", "admin")


def _configured_password() -> str:
    return os.getenv("DAIRYOS_ADMIN_PASSWORD", "dairyos")


def _configured_role() -> str:
    return os.getenv("DAIRYOS_ADMIN_ROLE", "admin")


def _signing_secret() -> bytes:
    secret = os.getenv("DAIRYOS_AUTH_SECRET")
    if not secret:
        if os.getenv("DAIRYOS_ENV", "development").lower() == "production":
            raise RuntimeError("DAIRYOS_AUTH_SECRET must be configured in production")
        secret = "dairyos-development-secret"
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


@router.post("/login")
def login(credentials: LoginRequest | None = None):
    """Authenticate the configured farm administrator and issue a bearer token."""

    supplied = credentials or LoginRequest()
    expected_username = _configured_username()
    expected_password = _configured_password()

    if not hmac.compare_digest(supplied.username, expected_username) or not hmac.compare_digest(
        supplied.password, expected_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = int(time.time())
    claims = {
        "sub": supplied.username,
        "role": _configured_role(),
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
    """Return the authenticated operator when a bearer token is supplied.

    Existing farm-floor forms remain backward compatible while authenticated
    clients gain authoritative server-side operator attribution. A supplied but
    invalid bearer token is still rejected rather than silently falling back to
    an operator value supplied by the client.
    """

    if credentials is None:
        return None
    return _decode_token(credentials.credentials)


@router.get("/me")
def current_user(user: dict[str, Any] = Depends(get_current_user)):
    """Return the authenticated operator identity and role."""

    return {
        "username": user["sub"],
        "role": user["role"],
        "issued_at": user["iat"],
        "expires_at": user["exp"],
    }
