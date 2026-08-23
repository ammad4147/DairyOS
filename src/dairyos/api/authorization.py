from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from dairyos.api.auth import _decode_token, get_current_user, require_role
from dairyos.auth.permissions import PERMISSIONS, ROLE_DESCRIPTIONS, ROLE_PERMISSIONS, has_permission, normalize_permissions, permissions_for_role
from dairyos.data.repositories.repository_factory import RepositoryFactory

router = APIRouter(prefix="/authz", tags=["authorization"])


def authorization_is_enforced() -> bool:
    explicit = os.getenv("DAIRYOS_ENFORCE_AUTHZ")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes", "on"}
    environment = os.getenv("DAIRYOS_ENV", "development").strip().lower()
    return environment in {"production", "staging", "preprod"}


def permission_for_request(method: str, path: str, payload: dict[str, Any] | None = None) -> str | None:
    m = method.upper()
    clean = path.rstrip("/") or "/"
    if clean.startswith("/authz") or clean in {"/login", "/me", "/auth/users", "/auth/users/"}:
        return None
    if clean.startswith("/farm/finance-ledger"):
        if m == "GET": return "finance.view"
        if m == "POST" and clean.count("/") == 2:
            category = str((payload or {}).get("master_category") or "").upper()
            return "finance.create_opex" if category == "OPEX" else "finance.create_feed"
        if m == "PATCH": return "finance.edit"
        if m == "POST" and clean.endswith("/status"):
            return "finance.void" if str((payload or {}).get("status") or "").upper() == "VOID" else "finance.edit"
    if clean == "/farm/animals" or clean == "/farm/animals/":
        return {"GET": "animals.view", "POST": "animals.create"}.get(m)
    if clean.startswith("/farm/animals/"):
        if clean.endswith("/disposition"): return "animals.disposition"
        return {"GET": "animals.view", "PATCH": "animals.edit"}.get(m)
    if clean == "/farm/milk" or clean.startswith("/farm/milk/"):
        return {"GET": "milk.view", "POST": "milk.create", "PATCH": "milk.edit"}.get(m)
    if clean.startswith("/farm/feed"):
        return {"GET": "feed.view", "POST": "feed.create", "PATCH": "feed.edit"}.get(m)
    if clean.startswith("/farm/breeding") or clean.startswith("/farm/reproduction"):
        return {"GET": "breeding.view", "POST": "breeding.create", "PATCH": "breeding.edit"}.get(m)
    if clean.startswith("/farm/health") or clean.startswith("/farm/treatments"):
        return {"GET": "health.view", "POST": "health.create", "PATCH": "health.edit"}.get(m)
    if clean.startswith("/farm/coml"): return "coml.view"
    if clean.startswith("/farm/analytics") or clean.startswith("/analytics"): return "analytics.view"
    if clean.startswith("/farm/audit") or clean.startswith("/audit"): return "audit.view"
    return None


def authorize_request(request: Request, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    required = permission_for_request(request.method, request.url.path, payload)
    if required is None: return None
    credentials = request.headers.get("Authorization")
    if not credentials or not credentials.lower().startswith("bearer "):
        if not authorization_is_enforced():
            return None
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    user = _decode_token(credentials.split(" ", 1)[1].strip())
    if not has_permission(str(user.get("role")), required):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission required: {required}")
    return user


@router.get("/permissions")
def current_permissions(user: dict[str, Any] = Depends(get_current_user)):
    role = str(user["role"]).upper()
    return {"role": role, "description": ROLE_DESCRIPTIONS.get(role, ""), "permissions": normalize_permissions(permissions_for_role(role))}


@router.get("/matrix")
def permission_matrix(_owner: dict[str, Any] = Depends(require_role("OWNER"))):
    return {"permissions": list(PERMISSIONS), "roles": {role: {"description": ROLE_DESCRIPTIONS[role], "permissions": normalize_permissions(permissions)} for role, permissions in ROLE_PERMISSIONS.items()}}


@router.patch("/users/{username}/active")
def set_user_active(username: str, payload: dict[str, bool], _owner: dict[str, Any] = Depends(require_role("OWNER"))):
    factory = RepositoryFactory.create()
    try:
        user = factory.users().get_by_username(username)
        if user is None: raise HTTPException(status_code=404, detail="User not found")
        if username == _owner["sub"] and payload.get("active") is False:
            raise HTTPException(status_code=409, detail="The current owner cannot disable their own account")
        user.active = bool(payload.get("active", True))
        factory.session.add(user)
        factory.session.commit()
        return {"username": user.username, "role": user.role, "active": user.active}
    finally:
        factory.close()
