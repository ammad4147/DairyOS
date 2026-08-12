"""Farm-scoped authentication and authorization."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dairyos.application.identity.models.authorization_role import AuthorizationRole
from dairyos.application.identity.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from dairyos.data.database.session import get_session


router = APIRouter(tags=["Authentication"])
TOKEN_TTL_SECONDS = 8 * 60 * 60


class LoginRequest(BaseModel):
    farm_id: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)


class UserCreateRequest(BaseModel):
    farm_id: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=12, max_length=256)
    role: AuthorizationRole


def _secret() -> bytes:
    value = os.getenv("DAIRYOS_AUTH_SECRET")
    if not value:
        raise RuntimeError("DAIRYOS_AUTH_SECRET must be configured")
    return value.encode("utf-8")


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256$310000${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _issue_token(context: dict[str, Any]) -> str:
    payload = {**context, "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    encoded = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _b64(hmac.new(_secret(), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def _decode_token(token: str) -> dict[str, Any]:
    try:
        encoded, signature = token.split(".", 1)
        expected = _b64(hmac.new(_secret(), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        payload = json.loads(_unb64(encoded))
        if int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError("expired token")
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_session),
) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    context = _decode_token(authorization.split(" ", 1)[1].strip())
    account = SqlAlchemyUserRepository(db).get_by_id(UUID(str(context["sub"])))
    if account is None or not account.active or account.farm_id != context.get("farm_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return SqlAlchemyUserRepository.to_context(account)


def get_optional_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_session),
) -> dict[str, Any] | None:
    if not authorization:
        return None
    return get_current_user(authorization=authorization, db=db)


def require_roles(*roles: AuthorizationRole):
    allowed = {role.value for role in roles}

    def dependency(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user.get("role") not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient authorization")
        return user

    return dependency


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_session)):
    account = SqlAlchemyUserRepository(db).get_by_username(
        farm_id=payload.farm_id, username=payload.username
    )
    if account is None or not account.active or not _verify_password(
        payload.password, account.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    context = SqlAlchemyUserRepository.to_context(account)
    return {
        "access_token": _issue_token(context),
        "token_type": "bearer",
        "expires_in": TOKEN_TTL_SECONDS,
        "user": context,
    }


@router.post("/users")
def create_user(
    payload: UserCreateRequest,
    current_user: dict[str, Any] = Depends(
        require_roles(AuthorizationRole.OWNER, AuthorizationRole.MANAGER)
    ),
    db: Session = Depends(get_session),
):
    if payload.farm_id != current_user["farm_id"]:
        raise HTTPException(status_code=403, detail="Cross-farm user creation is forbidden")
    if current_user["role"] == AuthorizationRole.MANAGER.value and payload.role == AuthorizationRole.OWNER:
        raise HTTPException(status_code=403, detail="Only an owner can create another owner")

    repo = SqlAlchemyUserRepository(db)
    if repo.get_by_username(farm_id=payload.farm_id, username=payload.username):
        raise HTTPException(status_code=409, detail="Username already exists in this farm")

    account = repo.create(
        farm_id=payload.farm_id,
        username=payload.username,
        display_name=payload.display_name,
        password_hash=_hash_password(payload.password),
        role=payload.role,
    )
    return repo.to_context(account)


@router.get("/me")
def me(current_user: dict[str, Any] = Depends(get_current_user)):
    return current_user
