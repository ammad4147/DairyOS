"""Controlled human access layered on top of the native desktop session."""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import timedelta
from types import SimpleNamespace
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from dairyos.core.time_utils import utcnow
from dairyos.data.models.human_identity import HumanIdentity, HumanSession
from dairyos.data.repositories.repository_factory import RepositoryFactory

router = APIRouter(prefix="/human-access", tags=["Human access"])

GROUPS = {
    "MANAGEMENT": ("Management & Professional Access", "MANAGER"),
    "MILK_OPERATOR": ("Milk Operations", "MILKER"),
    "ACCOUNTS_OPERATOR": ("Finance Entry", "ACCOUNTS_OPERATOR"),
}
PIN_ITERATIONS = 200_000
SESSION_HOURS = 8
MAX_PIN_FAILURES = 5
LOCKOUT_MINUTES = 15


def _audit(factory: RepositoryFactory, event_type: str, actor: str, detail: str) -> None:
    factory.operational_events().add(SimpleNamespace(event_type=event_type, source="HUMAN_ACCESS", description=f"{detail} actor={actor}", timestamp=utcnow(), actor=actor))


class BootstrapRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    pin: str
    pin_confirmation: str


class PersonRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    entry_group: str
    role: str | None = None

    @field_validator("entry_group")
    @classmethod
    def valid_group(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in GROUPS:
            raise ValueError("Unknown entry group")
        return value


class PinRequest(BaseModel):
    pin: str
    pin_confirmation: str | None = None


class InitialPinRequest(PinRequest):
    """Self-service first PIN for an active identity without a PIN."""


class LoginRequest(BaseModel):
    identity_id: int
    pin: str


class HelpRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=1000)


def _validate_pin(pin: str, confirmation: str | None = None) -> str:
    if not pin.isdigit() or len(pin) != 4:
        raise HTTPException(status_code=422, detail="PIN must contain exactly four digits")
    if confirmation is not None and pin != confirmation:
        raise HTTPException(status_code=422, detail="PIN confirmation does not match")
    return pin


def _hash_pin(pin: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), PIN_ITERATIONS)
    return base64.urlsafe_b64encode(digest).decode(), salt


def _verify_pin(pin: str, digest: str, salt: str) -> bool:
    candidate, _ = _hash_pin(pin, salt)
    return hmac.compare_digest(candidate, digest)


def _public_identity(identity: HumanIdentity) -> dict[str, Any]:
    return {
        "id": identity.id,
        "display_name": identity.display_name,
        "workspace": identity.entry_group,
        "entry_group": identity.entry_group,
        "role": identity.role,
        "active": bool(identity.active),
        "pin_set": bool(identity.pin_hash and identity.pin_salt),
    }


def _session_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _current_session(token: str | None) -> tuple[HumanSession, HumanIdentity]:
    if not token:
        raise HTTPException(status_code=401, detail="Human authentication required")
    factory = RepositoryFactory.create()
    try:
        row = factory.session.query(HumanSession).filter_by(session_hash=_session_hash(token)).first()
        if row is None or row.revoked_at is not None or row.expires_at <= utcnow():
            raise HTTPException(status_code=401, detail="Human session is invalid or expired")
        identity = factory.session.get(HumanIdentity, row.identity_id)
        if identity is None or not identity.active:
            raise HTTPException(status_code=403, detail="Identity is inactive")
        return row, identity
    finally:
        factory.close()


def _require_admin(token: str | None) -> tuple[HumanSession, HumanIdentity]:
    session, identity = _current_session(token)
    if identity.role != "PRIMARY_ADMIN":
        raise HTTPException(status_code=403, detail="Primary Administrator authority required")
    return session, identity


@router.get("/status")
def access_status() -> dict[str, Any]:
    factory = RepositoryFactory.create()
    try:
        identities = factory.session.query(HumanIdentity).all()
        primary = [x for x in identities if x.role == "PRIMARY_ADMIN" and x.active]
        return {"bootstrap_required": not primary, "bootstrap_complete": bool(primary), "entry_groups": [{"id": key, "label": value[0]} for key, value in GROUPS.items()]}
    finally:
        factory.close()


@router.post("/help")
def request_help(payload: HelpRequest) -> dict[str, Any]:
    """Record an access-assistance request without granting or resetting access."""
    factory = RepositoryFactory.create()
    try:
        _audit(
            factory,
            "human_access_help_requested",
            payload.display_name.strip(),
            f"Administrator review requested: {payload.message.strip()}",
        )
        return {"recorded": True, "status": "PENDING_ADMIN_REVIEW"}
    finally:
        factory.close()


@router.post("/bootstrap")
def bootstrap(payload: BootstrapRequest) -> dict[str, Any]:
    pin = _validate_pin(payload.pin, payload.pin_confirmation)
    factory = RepositoryFactory.create()
    try:
        if factory.session.query(HumanIdentity).filter_by(role="PRIMARY_ADMIN", active=True).first() is not None:
            raise HTTPException(status_code=409, detail="Primary Administrator already exists")
        digest, salt = _hash_pin(pin)
        identity = HumanIdentity(display_name=payload.display_name.strip(), entry_group="MANAGEMENT", role="PRIMARY_ADMIN", pin_hash=digest, pin_salt=salt)
        factory.session.add(identity)
        factory.session.commit()
        factory.session.refresh(identity)
        _audit(factory, "primary_admin_bootstrap", identity.display_name, "Primary Administrator established")
        return _public_identity(identity)
    finally:
        factory.close()


@router.get("/people")
def people(entry_group: str | None = None) -> dict[str, Any]:
    factory = RepositoryFactory.create()
    try:
        query = factory.session.query(HumanIdentity).filter_by(active=True)
        if entry_group:
            query = query.filter_by(entry_group=entry_group.strip().upper())
        return {"people": [_public_identity(row) for row in query.order_by(HumanIdentity.display_name).all()]}
    finally:
        factory.close()


@router.post("/people")
def create_person(payload: PersonRequest, x_dairyos_human_session: str | None = Header(default=None)) -> dict[str, Any]:
    _, current = _require_admin(x_dairyos_human_session)
    role = payload.role or GROUPS[payload.entry_group][1]
    factory = RepositoryFactory.create()
    try:
        identity = HumanIdentity(display_name=payload.display_name.strip(), entry_group=payload.entry_group, role=role)
        factory.session.add(identity)
        factory.session.commit()
        factory.session.refresh(identity)
        _audit(factory, "identity_created", current.display_name, f"Identity created id={identity.id} group={identity.entry_group} role={identity.role}")
        return _public_identity(identity)
    finally:
        factory.close()


@router.post("/people/{identity_id}/pin")
def set_pin(identity_id: int, payload: PinRequest, x_dairyos_human_session: str | None = Header(default=None)) -> dict[str, Any]:
    _session, current = _current_session(x_dairyos_human_session)
    if current.id != identity_id and current.role != "PRIMARY_ADMIN":
        raise HTTPException(status_code=403, detail="Cannot set another identity's PIN")
    pin = _validate_pin(payload.pin, payload.pin_confirmation)
    factory = RepositoryFactory.create()
    try:
        identity = factory.session.get(HumanIdentity, identity_id)
        if identity is None or not identity.active:
            raise HTTPException(status_code=404, detail="Identity not found")
        identity.pin_hash, identity.pin_salt = _hash_pin(pin)
        identity.failed_pin_attempts = 0
        identity.locked_until = None
        factory.session.add(identity)
        factory.session.commit()
        _audit(factory, "pin_established", current.display_name, f"PIN established for identity id={identity.id}")
        return _public_identity(identity)
    finally:
        factory.close()


@router.post("/people/{identity_id}/pin/initial")
def establish_initial_pin(
    identity_id: int,
    payload: InitialPinRequest,
    x_dairyos_human_session: str | None = Header(default=None),
) -> dict[str, Any]:
    _, current = _require_admin(x_dairyos_human_session)
    pin = _validate_pin(payload.pin, payload.pin_confirmation)
    factory = RepositoryFactory.create()
    try:
        identity = factory.session.get(HumanIdentity, identity_id)
        if identity is None or not identity.active:
            raise HTTPException(status_code=404, detail="Identity not found")
        if identity.pin_hash or identity.pin_salt:
            raise HTTPException(status_code=409, detail="Initial PIN setup is unavailable")
        identity.pin_hash, identity.pin_salt = _hash_pin(pin)
        factory.session.add(identity)
        factory.session.commit()
        _audit(factory, "pin_established", current.display_name, f"Initial PIN established for identity id={identity.id}")
        return _public_identity(identity)
    finally:
        factory.close()


@router.patch("/people/{identity_id}/active")
def set_active(identity_id: int, active: bool, x_dairyos_human_session: str | None = Header(default=None)) -> dict[str, Any]:
    _, current = _require_admin(x_dairyos_human_session)
    factory = RepositoryFactory.create()
    try:
        identity = factory.session.get(HumanIdentity, identity_id)
        if identity is None:
            raise HTTPException(status_code=404, detail="Identity not found")
        if identity.id == current.id and not active:
            raise HTTPException(status_code=409, detail="The current Primary Administrator cannot be deactivated")
        identity.active = bool(active)
        factory.session.add(identity)
        factory.session.commit()
        _audit(factory, "identity_activation" if active else "identity_deactivation", current.display_name, f"Identity id={identity.id} active={bool(active)}")
        return _public_identity(identity)
    finally:
        factory.close()


@router.post("/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    pin = _validate_pin(payload.pin)
    factory = RepositoryFactory.create()
    try:
        identity = factory.session.get(HumanIdentity, payload.identity_id)
        now = utcnow()
        if identity is None or not identity.active:
            raise HTTPException(status_code=401, detail="Identity is unavailable")
        if identity.locked_until and identity.locked_until > now:
            raise HTTPException(status_code=423, detail="Identity temporarily locked")
        if not identity.pin_hash or not identity.pin_salt:
            raise HTTPException(status_code=409, detail="PIN setup required")
        if not _verify_pin(pin, identity.pin_hash, identity.pin_salt):
            identity.failed_pin_attempts += 1
            if identity.failed_pin_attempts >= MAX_PIN_FAILURES:
                identity.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
                identity.failed_pin_attempts = 0
            factory.session.commit()
            _audit(factory, "human_login_failure", identity.display_name, f"PIN authentication failed identity_id={identity.id}")
            raise HTTPException(status_code=401, detail="Invalid PIN")
        identity.failed_pin_attempts = 0
        identity.locked_until = None
        token = secrets.token_urlsafe(32)
        row = HumanSession(session_hash=_session_hash(token), identity_id=identity.id, role=identity.role, entry_group=identity.entry_group, expires_at=now + timedelta(hours=SESSION_HOURS))
        factory.session.add(row)
        factory.session.commit()
        _audit(factory, "human_login_success", identity.display_name, f"Human session created identity_id={identity.id} group={identity.entry_group}")
        return {"session_token": token, "expires_at": row.expires_at, "identity": _public_identity(identity)}
    finally:
        factory.close()


@router.get("/me")
def me(x_dairyos_human_session: str | None = Header(default=None)) -> dict[str, Any]:
    _, identity = _current_session(x_dairyos_human_session)
    return {"identity": _public_identity(identity)}


@router.post("/logout")
def logout(x_dairyos_human_session: str | None = Header(default=None)) -> dict[str, bool]:
    session, _ = _current_session(x_dairyos_human_session)
    factory = RepositoryFactory.create()
    try:
        row = factory.session.get(HumanSession, session.id)
        row.revoked_at = utcnow()
        factory.session.commit()
        _audit(factory, "human_logout", str(session.identity_id), f"Human session revoked identity_id={session.identity_id}")
        return {"logged_out": True}
    finally:
        factory.close()
