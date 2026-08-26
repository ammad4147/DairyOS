from __future__ import annotations

import os
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from dairyos.api.auth import _decode_token, get_current_user, require_permission
from dairyos.auth.permissions import PERMISSIONS, PERMISSION_GROUPS, ROLE_DESCRIPTIONS, ROLE_PERMISSIONS, normalize_permissions, permissions_for_role, permissions_from_json
from dairyos.data.repositories.repository_factory import RepositoryFactory

router = APIRouter(prefix="/authz", tags=["authorization"])


def _resolved_permissions(user: dict[str, Any]) -> frozenset[str]:
    factory = RepositoryFactory.create()
    try:
        persisted = factory.users().get_by_username(str(user["sub"]))
        if persisted is not None:
            return permissions_from_json(persisted.permissions_json, persisted.role)
    finally:
        factory.close()
    return permissions_for_role(str(user.get("role") or ""))


def permission_for_request(method: str, path: str, payload: dict[str, Any] | None = None) -> str | None:
    m = method.upper()
    clean = path.rstrip("/") or "/"
    if clean.startswith("/authz") or clean in {"/login", "/me", "/auth/users", "/auth/users/"}:
        return None
    if clean == "/dashboard" or clean.startswith("/dashboard/"):
        return "dashboard.view"
    if clean.startswith("/farm/finance-ledger") or clean.startswith("/farm/finance") or clean.startswith("/farm/financial") or clean.startswith("/financial"):
        if m == "GET": return "finance.view"
        if m == "POST" and clean.count("/") == 2:
            category = str((payload or {}).get("master_category") or "").upper()
            return "finance.create_opex" if category == "OPEX" else "finance.create_feed"
        if m == "PATCH": return "finance.edit"
        if m == "POST" and clean.endswith("/status"):
            return "finance.void" if str((payload or {}).get("status") or "").upper() == "VOID" else "finance.edit"
    if clean == "/farm/animals" or clean == "/farm/animals/": return {"GET": "animals.view", "POST": "animals.create"}.get(m)
    if clean.startswith("/farm/animals/"):
        if clean.endswith("/disposition"): return "animals.disposition"
        return {"GET": "animals.view", "PATCH": "animals.edit"}.get(m)
    if clean == "/farm/milk" or clean.startswith("/farm/milk/"): return {"GET": "milk.view", "POST": "milk.create", "PATCH": "milk.edit"}.get(m)
    if clean.startswith("/farm/feed"): return {"GET": "feed.view", "POST": "feed.create", "PATCH": "feed.edit"}.get(m)
    if clean.startswith("/farm/breeding") or clean.startswith("/farm/reproduction"): return {"GET": "breeding.view", "POST": "breeding.create", "PATCH": "breeding.edit"}.get(m)
    if clean.startswith("/farm/health") or clean.startswith("/farm/treatments"): return {"GET": "health.view", "POST": "health.create", "PATCH": "health.edit"}.get(m)
    if clean.startswith("/farm/coml"): return "coml.view"
    if clean.startswith("/farm/analytics") or clean.startswith("/analytics"): return "analytics.view"
    if clean.startswith("/farm/audit") or clean.startswith("/audit"): return "audit.view"
    return None


def _deployment_enforcement_enabled() -> bool:
    explicit = os.getenv("DAIRYOS_ENFORCE_AUTHZ")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes", "on"}
    return os.getenv("DAIRYOS_ENV", "development").strip().lower() != "development"


def authorize_request(request: Request, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    required = permission_for_request(request.method, request.url.path, payload)
    if required is None:
        return None
    credentials = request.headers.get("Authorization")
    if not credentials or not credentials.lower().startswith("bearer "):
        if _deployment_enforcement_enabled():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
        return None
    user = _decode_token(credentials.split(" ", 1)[1].strip())
    permissions = _resolved_permissions(user)
    if required in permissions:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission required: {required}")


@router.get("/permissions")
def current_permissions(user: dict[str, Any] = Depends(get_current_user)):
    role = str(user["role"]).upper()
    permissions = _resolved_permissions(user)
    return {"role": role, "description": ROLE_DESCRIPTIONS.get(role, "Custom user access profile."), "permissions": normalize_permissions(permissions)}


@router.get("/matrix")
def permission_matrix(_admin: dict[str, Any] = Depends(require_permission("users.permissions"))):
    return {"permissions": list(PERMISSIONS), "groups": {name: list(values) for name, values in PERMISSION_GROUPS.items()}, "roles": {role: {"description": ROLE_DESCRIPTIONS[role], "permissions": normalize_permissions(permissions)} for role, permissions in ROLE_PERMISSIONS.items()}}


class UserAccessProfile(BaseModel):
    job_title: str | None = Field(default=None, max_length=120)
    personal_email: str | None = None
    permissions: list[str] = Field(default_factory=list)

    @field_validator("personal_email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip(): return None
        value = value.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("personal_email must be a valid email address")
        return value


@router.get("/users/{username}/profile")
def get_user_profile(username: str, _admin: dict[str, Any] = Depends(require_permission("users.view"))):
    factory = RepositoryFactory.create()
    try:
        user = factory.users().get_by_username(username)
        if user is None: raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "username": user.username, "role": user.role, "job_title": user.job_title, "personal_email": user.personal_email, "active": user.active, "permissions": normalize_permissions(permissions_from_json(user.permissions_json, user.role))}
    finally:
        factory.close()


@router.put("/users/{username}/profile")
def update_user_profile(username: str, payload: UserAccessProfile, _admin: dict[str, Any] = Depends(require_permission("users.edit"))):
    import json
    factory = RepositoryFactory.create()
    try:
        user = factory.users().get_by_username(username)
        if user is None: raise HTTPException(status_code=404, detail="User not found")
        normalized = normalize_permissions(payload.permissions)
        user.job_title = payload.job_title.strip() if payload.job_title else None
        user.personal_email = payload.personal_email
        user.permissions_json = json.dumps(normalized, separators=(",", ":"))
        factory.session.add(user)
        factory.session.commit()
        return {"username": user.username, "job_title": user.job_title, "personal_email": user.personal_email, "permissions": normalized}
    finally:
        factory.close()


@router.patch("/users/{username}/active")
def set_user_active(username: str, payload: dict[str, bool], _admin: dict[str, Any] = Depends(require_permission("users.disable"))):
    factory = RepositoryFactory.create()
    try:
        user = factory.users().get_by_username(username)
        if user is None: raise HTTPException(status_code=404, detail="User not found")
        if username == _admin["sub"] and payload.get("active") is False: raise HTTPException(status_code=409, detail="The current administrator cannot disable their own account")
        user.active = bool(payload.get("active", True))
        factory.session.add(user)
        factory.session.commit()
        return {"username": user.username, "role": user.role, "job_title": user.job_title, "personal_email": user.personal_email, "active": user.active}
    finally:
        factory.close()
