"""Operational authentication and role identity for DairyOS."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from dairyos.api.reference_data import GOVERNED
from dairyos.auth.permissions import permissions_from_json, permissions_for_role
from dairyos.data.repositories.repository_factory import RepositoryFactory

# Authentication endpoints are intentionally namespaced under /auth.  This
# matches the production API contract used by the operator shell and by the
# authorization middleware (which treats /auth/users and /auth/login as public
# identity-establishment routes).  Keeping the namespace here, rather than
# relying on an app-level prefix, also makes the router safe to mount in tests
# and other ASGI compositions.
router = APIRouter(prefix="/auth", tags=["Authentication"])
_bearer = HTTPBearer(auto_error=False)
_PBKDF2_ITERATIONS = 200_000
_LEGACY_ADMIN_PASSWORD_HASH_KEY = "legacy_admin_password_hash"
_LEGACY_ADMIN_PASSWORD_SALT_KEY = "legacy_admin_password_salt"


class LoginRequest(BaseModel):
    username: str = Field(default="admin", min_length=1)
    password: str = Field(default="dairyos", min_length=1)


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    role: str = Field(default="CUSTOM", min_length=1)


def _configured_username() -> str:
    return os.getenv("DAIRYOS_ADMIN_USERNAME", "admin")


def _configured_password() -> str:
    return os.getenv("DAIRYOS_ADMIN_PASSWORD", "dairyos")


def _configured_role() -> str:
    """Return the role of the bootstrap account.

    The configured legacy/bootstrap account is always the system Admin.
    Farm ownership is a separate persisted identity and must never be inferred
    from the bootstrap username or from an environment override.
    """
    return "ADMIN"


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
        expected_signature = hmac.new(_signing_secret(), encoded.encode("ascii"), hashlib.sha256).digest()
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token", headers={"WWW-Authenticate": "Bearer"}) from None


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS)
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


def _legacy_admin_password_override() -> tuple[str, str] | None:
    factory = RepositoryFactory.create()
    try:
        repository = factory.app_settings()
        password_hash = repository.get(_LEGACY_ADMIN_PASSWORD_HASH_KEY)
        salt = repository.get(_LEGACY_ADMIN_PASSWORD_SALT_KEY)
        if password_hash and salt:
            return str(password_hash), str(salt)
        return None
    finally:
        factory.close()


def _verify_legacy_admin_password(password: str) -> bool:
    override = _legacy_admin_password_override()
    if override is not None:
        return _verify_password(password, override[0], override[1])
    return hmac.compare_digest(password, _configured_password())


def _resolved_permissions_for_identity(user: dict[str, Any]) -> frozenset[str]:
    factory = RepositoryFactory.create()
    try:
        persisted = factory.users().get_by_username(str(user.get("sub") or ""))
        if persisted is not None:
            return permissions_from_json(persisted.permissions_json, persisted.role)
    finally:
        factory.close()
    return permissions_for_role(str(user.get("role") or ""))


@router.post("/login")
def login(credentials: LoginRequest | None = None):
    supplied = credentials or LoginRequest()
    persisted_user = _find_persisted_user(supplied.username)
    if persisted_user is not None:
        if not persisted_user.active or not _verify_password(supplied.password, persisted_user.password_hash, persisted_user.password_salt):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"})
        role = persisted_user.role
    else:
        if not hmac.compare_digest(supplied.username, _configured_username()) or not _verify_legacy_admin_password(supplied.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"})
        role = _configured_role()
    now = int(time.time())
    claims = {"sub": supplied.username, "role": role, "iat": now, "exp": now + int(os.getenv("DAIRYOS_AUTH_TOKEN_TTL", "28800"))}
    return {"access_token": _encode_token(claims), "token_type": "bearer", "user": {"username": supplied.username, "role": claims["role"]}, "expires_at": claims["exp"]}


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    return _decode_token(credentials.credentials)


def get_optional_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict[str, Any] | None:
    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token", headers={"WWW-Authenticate": "Bearer"})
    return _decode_token(credentials.credentials)


def require_role(*allowed_roles: str):
    def _dependency(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this action")
        return user
    return _dependency


def require_permission(permission: str):
    def _dependency(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if permission not in _resolved_permissions_for_identity(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission required: {permission}")
        return user
    return _dependency


@router.get("/me")
def current_user(user: dict[str, Any] = Depends(get_current_user)):
    return {"username": user["sub"], "role": user["role"], "issued_at": user["iat"], "expires_at": user["exp"]}


@router.post("/users")
def create_user(payload: CreateUserRequest, _admin: dict[str, Any] = Depends(require_permission("users.create"))):
    if payload.role not in GOVERNED["auth_roles"]:
        raise HTTPException(status_code=422, detail=f"role must be one of {GOVERNED['auth_roles']}")
    factory = RepositoryFactory.create()
    try:
        users = factory.users()
        if users.exists_username(payload.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this username already exists")
        from dairyos.data.models.user import User
        password_hash, salt = _hash_password(payload.password)
        created = users.add(User(username=payload.username, password_hash=password_hash, password_salt=salt, role=payload.role, active=True))
        return {"id": created.id, "username": created.username, "role": created.role, "active": created.active}
    finally:
        factory.close()


@router.patch("/users/{username}/password")
def reset_user_password(username: str, payload: dict[str, str] = Body(...), _admin: dict[str, Any] = Depends(require_permission("users.edit"))):
    factory = RepositoryFactory.create()
    try:
        user = factory.users().get_by_username(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        new_password = payload.get("password", "")
        if not new_password:
            raise HTTPException(status_code=422, detail="password is required")
        password_hash, salt = _hash_password(new_password)
        user.password_hash = password_hash
        user.password_salt = salt
        factory.session.add(user)
        factory.session.commit()
        return {"username": user.username, "role": user.role, "active": user.active, "password_reset": True}
    finally:
        factory.close()


@router.post("/me/password")
def change_my_password(payload: dict[str, str] = Body(...), current_user: dict[str, Any] = Depends(get_current_user)):
    current_password = payload.get("current_password", "")
    new_password = payload.get("new_password", "")
    if not current_password or not new_password:
        raise HTTPException(status_code=422, detail="current_password and new_password are required")

    username = str(current_user["sub"])
    factory = RepositoryFactory.create()
    try:
        user = factory.users().get_by_username(username)
        if user is not None:
            if not _verify_password(current_password, user.password_hash, user.password_salt):
                raise HTTPException(status_code=401, detail="Current password is incorrect", headers={"WWW-Authenticate": "Bearer"})
            password_hash, salt = _hash_password(new_password)
            user.password_hash = password_hash
            user.password_salt = salt
            factory.session.add(user)
            factory.session.commit()
            return {"username": user.username, "password_changed": True, "account_type": "persisted"}

        if username != _configured_username():
            raise HTTPException(status_code=404, detail="Persisted user account not found")
        if not _verify_legacy_admin_password(current_password):
            raise HTTPException(status_code=401, detail="Current password is incorrect", headers={"WWW-Authenticate": "Bearer"})

        password_hash, salt = _hash_password(new_password)
        settings = factory.app_settings()
        settings.set(_LEGACY_ADMIN_PASSWORD_HASH_KEY, password_hash, updated_by=username)
        settings.set(_LEGACY_ADMIN_PASSWORD_SALT_KEY, salt, updated_by=username)
        return {"username": username, "password_changed": True, "account_type": "legacy_admin"}
    finally:
        factory.close()


@router.get("/users")
def list_users(_admin: dict[str, Any] = Depends(require_permission("users.view"))):
    factory = RepositoryFactory.create()
    try:
        return {"users": [{"id": u.id, "username": u.username, "role": u.role, "active": u.active} for u in factory.users().get_all()]}
    finally:
        factory.close()
