"""Settings endpoints, including deployment lifecycle controls."""

from __future__ import annotations

import secrets
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from dairyos.api.auth import (
    _DEFAULT_ADMIN_PASSWORD,
    _LEGACY_ADMIN_PASSWORD_HASH_KEY,
    _LEGACY_ADMIN_PASSWORD_SALT_KEY,
    _configured_password,
    _configured_username,
    _find_persisted_user,
    _hash_password,
    _legacy_admin_password_override,
    _verify_password,
    require_permission,
)
from dairyos.api.dependencies import get_container
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.email.service import EmailService
from dairyos.farm.settings.services.deployment_control_service import DeploymentControlService
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])

_NAVIGATION_RECOVERY_HASH_KEY = "navigation_admin_recovery_hash"
_NAVIGATION_RECOVERY_SALT_KEY = "navigation_admin_recovery_salt"
_MIN_ADMIN_PASSWORD_LENGTH = 12


def _service() -> tuple[FarmSettingsService, RepositoryFactory]:
    rf = RepositoryFactory.create()
    return FarmSettingsService(rf.app_settings()), rf


def _deployment_service() -> tuple[DeploymentControlService, RepositoryFactory]:
    service, rf = _service()
    return DeploymentControlService(service), rf


def _navigation_credential_status() -> dict[str, object]:
    username = _configured_username()
    persisted_user = _find_persisted_user(username)
    password_override = _legacy_admin_password_override()
    factory = RepositoryFactory.create()
    try:
        settings = factory.app_settings()
        recovery_configured = bool(
            settings.get(_NAVIGATION_RECOVERY_HASH_KEY)
            and settings.get(_NAVIGATION_RECOVERY_SALT_KEY)
        )
    finally:
        factory.close()

    setup_required = (
        persisted_user is None
        and password_override is None
        and _configured_password() == _DEFAULT_ADMIN_PASSWORD
    )
    return {
        "username": username,
        "setup_required": setup_required,
        "recovery_configured": recovery_configured,
    }


def _require_local_console(request: Request) -> None:
    host = request.client.host if request.client is not None else ""
    if host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
        raise HTTPException(
            status_code=403,
            detail=(
                "Administrator credential setup and recovery are available "
                "only from the local DairyOS computer."
            ),
        )


def _validate_admin_password(password: str) -> None:
    if len(password) < _MIN_ADMIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=(
                "Administrator password must be at least "
                f"{_MIN_ADMIN_PASSWORD_LENGTH} characters long."
            ),
        )
    if password == _DEFAULT_ADMIN_PASSWORD:
        raise HTTPException(
            status_code=422,
            detail="The development default password may not be used.",
        )


def _persist_legacy_admin_password(
    settings,
    password: str,
    *,
    updated_by: str,
) -> None:
    password_hash, salt = _hash_password(password)
    settings.set(
        _LEGACY_ADMIN_PASSWORD_HASH_KEY,
        password_hash,
        updated_by=updated_by,
    )
    settings.set(
        _LEGACY_ADMIN_PASSWORD_SALT_KEY,
        salt,
        updated_by=updated_by,
    )


def _rotate_recovery_code(settings, *, updated_by: str) -> str:
    recovery_code = secrets.token_urlsafe(24)
    recovery_hash, recovery_salt = _hash_password(recovery_code)
    settings.set(
        _NAVIGATION_RECOVERY_HASH_KEY,
        recovery_hash,
        updated_by=updated_by,
    )
    settings.set(
        _NAVIGATION_RECOVERY_SALT_KEY,
        recovery_salt,
        updated_by=updated_by,
    )
    return recovery_code


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


class UpdateNavigationPreferencesRequest(BaseModel):
    hidden_tabs: list[str] = Field(default_factory=list)


class NavigationCredentialSetupRequest(BaseModel):
    username: str = Field(min_length=1)
    new_password: str = Field(min_length=1)


class NavigationCredentialRecoveryRequest(BaseModel):
    username: str = Field(min_length=1)
    recovery_code: str = Field(min_length=1)
    new_password: str = Field(min_length=1)


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


@router.get("/navigation-credentials")
def navigation_credential_status():
    return _navigation_credential_status()


@router.post("/navigation-credentials/setup")
def setup_navigation_credentials(
    payload: NavigationCredentialSetupRequest,
    request: Request,
):
    _require_local_console(request)
    status_payload = _navigation_credential_status()
    if not bool(status_payload["setup_required"]):
        raise HTTPException(
            status_code=409,
            detail="Administrator password has already been configured.",
        )
    if payload.username != _configured_username():
        raise HTTPException(status_code=422, detail="Administrator username does not match this DairyOS installation.")
    _validate_admin_password(payload.new_password)

    factory = RepositoryFactory.create()
    try:
        settings = factory.app_settings()
        _persist_legacy_admin_password(
            settings,
            payload.new_password,
            updated_by="navigation-initial-setup",
        )
        recovery_code = _rotate_recovery_code(
            settings,
            updated_by="navigation-initial-setup",
        )
        return {
            "username": payload.username,
            "password_configured": True,
            "recovery_configured": True,
            "recovery_code": recovery_code,
            "recovery_code_display": "ONE_TIME",
        }
    finally:
        factory.close()


@router.post("/navigation-credentials/recover")
def recover_navigation_credentials(
    payload: NavigationCredentialRecoveryRequest,
    request: Request,
):
    _require_local_console(request)
    if payload.username != _configured_username():
        raise HTTPException(status_code=401, detail="Invalid administrator recovery credentials.")
    _validate_admin_password(payload.new_password)

    factory = RepositoryFactory.create()
    try:
        settings = factory.app_settings()
        recovery_hash = settings.get(_NAVIGATION_RECOVERY_HASH_KEY)
        recovery_salt = settings.get(_NAVIGATION_RECOVERY_SALT_KEY)
        if not recovery_hash or not recovery_salt:
            raise HTTPException(
                status_code=409,
                detail="No recovery code is configured. Unlock with the current password and generate one.",
            )
        if not _verify_password(
            payload.recovery_code,
            str(recovery_hash),
            str(recovery_salt),
        ):
            raise HTTPException(status_code=401, detail="Invalid administrator recovery credentials.")

        _persist_legacy_admin_password(
            settings,
            payload.new_password,
            updated_by="navigation-recovery",
        )
        recovery_code = _rotate_recovery_code(
            settings,
            updated_by="navigation-recovery",
        )
        return {
            "username": payload.username,
            "password_recovered": True,
            "recovery_code": recovery_code,
            "recovery_code_display": "ONE_TIME",
        }
    finally:
        factory.close()


@router.post("/navigation-credentials/recovery-code")
def rotate_navigation_recovery_code(
    admin=Depends(require_permission("settings.navigation")),
):
    factory = RepositoryFactory.create()
    try:
        recovery_code = _rotate_recovery_code(
            factory.app_settings(),
            updated_by=str(admin.get("sub") or "ADMIN"),
        )
        return {
            "username": str(admin.get("sub") or _configured_username()),
            "recovery_code": recovery_code,
            "recovery_code_display": "ONE_TIME",
        }
    finally:
        factory.close()


@router.put("/navigation")
def update_navigation_preferences(
    payload: UpdateNavigationPreferencesRequest,
    admin=Depends(require_permission("settings.navigation")),
):
    service, rf = _service()
    try:
        return service.update_navigation_preferences(
            hidden_tabs=payload.hidden_tabs,
            updated_by=str(admin.get("sub") or "ADMIN"),
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
        status_payload = service.activate(updated_by=payload.updated_by)
        return {"status": "deployed", "deployment": status_payload}
    finally:
        rf.close()


@router.post("/reset", include_in_schema=False)
@router.post("/reset-test-data", include_in_schema=False)
def reset_test_data(payload: ResetTestDataRequest, container=Depends(get_container)):
    """Reject the legacy in-application destructive reset path."""
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


class NotificationRecipient(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    designation: str = ""
    email: str = Field(min_length=3)


class NotificationRecipientsRequest(BaseModel):
    recipients: list[NotificationRecipient] = Field(default_factory=list)


_NOTIFICATION_RECIPIENTS_KEY = "email_notification_recipients"


@router.get("/email/recipients")
def get_email_recipients():
    factory = RepositoryFactory.create()
    try:
        raw = factory.app_settings().get(_NOTIFICATION_RECIPIENTS_KEY)
        if not raw:
            return {"recipients": []}
        try:
            parsed = json.loads(str(raw))
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = []
        return {"recipients": parsed if isinstance(parsed, list) else []}
    finally:
        factory.close()


@router.put("/email/recipients")
def save_email_recipients(payload: NotificationRecipientsRequest):
    normalized = []
    seen = set()
    for item in payload.recipients:
        email = item.email.strip().lower()
        if "@" not in email:
            raise HTTPException(status_code=422, detail=f"Invalid notification recipient email: {item.email}")
        if email in seen:
            continue
        seen.add(email)
        normalized.append(
            {
                "id": item.id,
                "name": item.name.strip(),
                "designation": item.designation.strip(),
                "email": email,
            }
        )
    factory = RepositoryFactory.create()
    try:
        factory.app_settings().set(
            _NOTIFICATION_RECIPIENTS_KEY,
            json.dumps(normalized, sort_keys=True),
            updated_by="UI Operator",
        )
        return {"recipients": normalized}
    finally:
        factory.close()


@router.get("/email")
def get_email_settings():
    return EmailService().public_config()


@router.put("/email")
def save_email_settings(payload: EmailSettingsRequest):
    try:
        return EmailService().save_config(
            payload.model_dump(),
            updated_by="UI Operator",
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/email/test")
def send_test_email(payload: EmailTestRequest):
    try:
        EmailService().send(
            recipient=payload.recipient,
            subject="DairyOS SMTP Test",
            body="DairyOS SMTP configuration test succeeded.",
        )
        return {"status": "sent", "recipient": payload.recipient}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SMTP test failed: {exc}") from exc
