"""Settings endpoints, including deployment lifecycle controls."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.auth import require_permission
from dairyos.api.dependencies import get_container
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.email.service import EmailService
from dairyos.farm.settings.services.deployment_control_service import DeploymentControlService
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])


def _service() -> tuple[FarmSettingsService, RepositoryFactory]:
    rf = RepositoryFactory.create()
    return FarmSettingsService(rf.app_settings()), rf


def _deployment_service() -> tuple[DeploymentControlService, RepositoryFactory]:
    service, rf = _service()
    return DeploymentControlService(service), rf


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


class ResetTestDataRequest(BaseModel):
    confirm: str
    updated_by: str = Field(default="UI Operator")


class DeployRequest(BaseModel):
    confirm: str
    updated_by: str = Field(default="UI Operator")


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
        return service.update_identity(
            farm_name=payload.farm_name,
            animal_id_prefix=payload.animal_id_prefix,
            updated_by=payload.updated_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


@router.put("/operational")
def update_operational_settings(payload: UpdateOperationalSettingsRequest):
    service, rf = _service()
    try:
        return service.update_operational_settings(
            timezone_name=payload.timezone,
            operational_date_convention=payload.operational_date_convention,
            updated_by=payload.updated_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


@router.put("/dashboard")
def update_dashboard_preferences(payload: UpdateDashboardPreferencesRequest):
    service, rf = _service()
    try:
        return service.update_dashboard_preferences(
            default_trend_period=payload.default_trend_period,
            card_visibility=payload.card_visibility,
            updated_by=payload.updated_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


@router.put("/alerts")
def update_alert_preferences(payload: UpdateAlertPreferencesRequest):
    service, rf = _service()
    try:
        return service.update_alert_preferences(
            preferences=payload.preferences,
            updated_by=payload.updated_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


@router.get("/deployment")
def deployment_status():
    service, rf = _deployment_service()
    try:
        return service.status()
    finally:
        rf.close()


@router.post("/deployment/activate")
def activate_deployment(payload: DeployRequest):
    if payload.confirm != "DEPLOY":
        raise HTTPException(
            status_code=422,
            detail='confirm must be the literal string "DEPLOY" to proceed',
        )

    service, rf = _deployment_service()
    try:
        status = service.activate(updated_by=payload.updated_by)
        return {"status": "deployed", "deployment": status}
    finally:
        rf.close()


@router.post("/reset", include_in_schema=False)
@router.post("/reset-test-data", include_in_schema=False)
def reset_test_data(payload: ResetTestDataRequest, container=Depends(get_container)):
    """Reject the legacy in-application destructive reset path.

    Reset is an administrative lifecycle operation and must be executed by the
    standalone DairyOS Administration Tool. Keeping this endpoint as a hard
    rejection prevents old clients from retaining a second destructive path.
    """
    raise HTTPException(
        status_code=410,
        detail=(
            "Application reset has moved to the standalone DairyOS "
            "Administration Tool. The operational application cannot perform "
            "destructive lifecycle reset operations."
        ),
    )


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
def get_email_settings(_admin=Depends(require_permission("settings.email"))):
    return EmailService().public_config()


@router.put("/email")
def save_email_settings(
    payload: EmailSettingsRequest,
    admin=Depends(require_permission("settings.email")),
):
    try:
        return EmailService().save_config(
            payload.model_dump(),
            updated_by=str(admin.get("sub") or "ADMIN"),
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/email/test")
def send_test_email(
    payload: EmailTestRequest,
    _admin=Depends(require_permission("settings.email")),
):
    try:
        EmailService().send(
            recipient=payload.recipient,
            subject="DairyOS SMTP Test",
            body="DairyOS SMTP configuration test succeeded.",
        )
        return {"status": "sent", "recipient": payload.recipient}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SMTP test failed: {exc}") from exc
