"""Settings endpoints (AA-013 §17, plus sender email administration)."""

from __future__ import annotations

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.auth import require_role
from dairyos.api.dependencies import get_container
from dairyos.data.database.session import engine
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.email.service import EmailService
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])

_PRESERVED_TABLES = {"alembic_version", "app_settings"}


def _service() -> tuple[FarmSettingsService, RepositoryFactory]:
    rf = RepositoryFactory.create()
    return FarmSettingsService(rf.app_settings()), rf


class UpdateIdentityRequest(BaseModel):
    farm_name: str | None = None
    animal_id_prefix: str | None = None
    updated_by: str = Field(default="UI Operator")


class UpdateOperationalSettingsRequest(BaseModel):
    timezone: str | None = None
    operational_date_convention: str | None = None
    updated_by: str = Field(default="UI Operator")


class UpdateDashboardPreferencesRequest(BaseModel):
    default_trend_period: str | None = None
    card_visibility: dict | None = None
    updated_by: str = Field(default="UI Operator")


class UpdateAlertPreferencesRequest(BaseModel):
    preferences: dict
    updated_by: str = Field(default="UI Operator")


class ResetProtectionRequest(BaseModel):
    enabled: bool
    password: str | None = None
    updated_by: str = Field(default="UI Operator")


class ResetTestDataRequest(BaseModel):
    confirm: str
    password: str | None = None


@router.get("")
def get_settings():
    service, rf = _service()
    try:
        return service.get_public_settings()
    finally:
        rf.close()


@router.put("")
def update_identity(payload: UpdateIdentityRequest):
    service, rf = _service()
    try:
        return service.update_identity(farm_name=payload.farm_name, animal_id_prefix=payload.animal_id_prefix, updated_by=payload.updated_by)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


@router.put("/operational")
def update_operational_settings(payload: UpdateOperationalSettingsRequest):
    service, rf = _service()
    try:
        return service.update_operational_settings(timezone_name=payload.timezone, operational_date_convention=payload.operational_date_convention, updated_by=payload.updated_by)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


@router.put("/dashboard")
def update_dashboard_preferences(payload: UpdateDashboardPreferencesRequest):
    service, rf = _service()
    try:
        return service.update_dashboard_preferences(default_trend_period=payload.default_trend_period, card_visibility=payload.card_visibility, updated_by=payload.updated_by)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


@router.put("/alerts")
def update_alert_preferences(payload: UpdateAlertPreferencesRequest):
    service, rf = _service()
    try:
        return service.update_alert_preferences(preferences=payload.preferences, updated_by=payload.updated_by)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


@router.post("/reset-protection")
def set_reset_protection(payload: ResetProtectionRequest):
    service, rf = _service()
    try:
        return service.set_reset_protection(enabled=payload.enabled, password=payload.password, updated_by=payload.updated_by)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


class EmailSettingsRequest(BaseModel):
    sender_email: str = Field(min_length=3)
    sender_display_name: str | None = None
    smtp_host: str = Field(min_length=1)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    use_tls: bool = True


class EmailTestRequest(BaseModel):
    recipient: str = Field(min_length=3)


@router.get("/email")
def get_email_settings(_owner=Depends(require_role("OWNER"))):
    return EmailService().public_config()


@router.put("/email")
def save_email_settings(payload: EmailSettingsRequest, owner=Depends(require_role("OWNER"))):
    try:
        return EmailService().save_config(payload.model_dump(), updated_by=str(owner.get("sub") or "OWNER"))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/email/test")
def send_test_email(payload: EmailTestRequest, _owner=Depends(require_role("OWNER"))):
    try:
        EmailService().send(recipient=payload.recipient, subject="DairyOS SMTP Test", body="DairyOS SMTP configuration test succeeded.")
        return {"status": "sent", "recipient": payload.recipient}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SMTP test failed: {exc}") from exc


def _truncate_all_operational_tables() -> list[str]:
    inspector = sa.inspect(engine)
    tables = [t for t in inspector.get_table_names() if t not in _PRESERVED_TABLES]
    if tables:
        quoted = ", ".join(f'"{t}"' for t in tables)
        with engine.begin() as conn:
            conn.execute(sa.text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
    return sorted(tables)


@router.post("/reset-test-data")
def reset_test_data(payload: ResetTestDataRequest, container=Depends(get_container)):
    if payload.confirm != "RESET":
        raise HTTPException(status_code=422, detail='confirm must be the literal string "RESET" to proceed')

    service, rf = _service()
    try:
        if service.is_reset_protected() and not service.verify_reset_password(payload.password):
            raise HTTPException(status_code=403, detail="Incorrect reset password")
    finally:
        rf.close()

    container_session = getattr(getattr(container, "repository_factory", None), "session", None)
    if container_session is not None:
        container_session.rollback()

    tables = _truncate_all_operational_tables()
    if getattr(container, "animal_operational_state_repository", None) is not None:
        container.animal_operational_state_repository.clear()
    if getattr(container, "operational_input_repository", None) is not None:
        container.operational_input_repository.clear()

    container.started = False
    container.operations = None
    container.dashboard = None
    return {"status": "reset", "tables_cleared": tables}
