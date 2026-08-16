"""Settings endpoints (AA-013 §17, 2026-08-14): farm identity, reset
protection, and the test-data reset action itself.

``POST /settings/reset-test-data`` truncates every real table in the
database except ``alembic_version`` (schema bookkeeping) and
``app_settings`` (these settings themselves -- a reset must not also wipe
the farm's own name/prefix/reset-password). This is deliberately table-
introspection-based rather than an explicit hand-maintained model list:
this project has more than once discovered a stray same-named table left
behind by an earlier experiment that a hand-maintained list would have
silently missed (the lesson behind the "self-healing migration" pattern
used across every migration since 20260814_03) -- truncating whatever
tables actually exist is the version of that same lesson applied to a
full data reset instead of a single migration.

Not currently password-protected by default: this farm is still in
build-out, and requiring a password before there is any UI to set one
would just lock the operator out. ``reset_protected`` (off by default,
settable from Settings) exists specifically for the moment this farm
goes live and accidental resets become costly.
"""

from __future__ import annotations

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.dependencies import get_container
from dairyos.data.database.session import engine
from dairyos.data.repositories.repository_factory import RepositoryFactory
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
def update_operational_settings(
    payload: UpdateOperationalSettingsRequest,
):
    service, rf = _service()

    try:
        return service.update_operational_settings(
            timezone_name=payload.timezone,
            operational_date_convention=(
                payload.operational_date_convention
            ),
            updated_by=payload.updated_by,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    finally:
        rf.close()


@router.put("/dashboard")
def update_dashboard_preferences(
    payload: UpdateDashboardPreferencesRequest,
):
    service, rf = _service()

    try:
        return service.update_dashboard_preferences(
            default_trend_period=(
                payload.default_trend_period
            ),
            card_visibility=payload.card_visibility,
            updated_by=payload.updated_by,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    finally:
        rf.close()


@router.put("/alerts")
def update_alert_preferences(
    payload: UpdateAlertPreferencesRequest,
):
    service, rf = _service()

    try:
        return service.update_alert_preferences(
            preferences=payload.preferences,
            updated_by=payload.updated_by,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    finally:
        rf.close()

@router.post("/reset-protection")
def set_reset_protection(payload: ResetProtectionRequest):
    service, rf = _service()
    try:
        return service.set_reset_protection(
            enabled=payload.enabled, password=payload.password, updated_by=payload.updated_by
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        rf.close()


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
        raise HTTPException(
            status_code=422,
            detail="confirm must be the literal string \"RESET\" to proceed",
        )

    service, rf = _service()
    try:
        if service.is_reset_protected() and not service.verify_reset_password(payload.password):
            raise HTTPException(status_code=403, detail="Incorrect reset password")
    finally:
        rf.close()

    # The running container holds one long-lived session across the whole
    # app lifetime (not one per request). A prior read on this same
    # session (e.g. an earlier GET in this session) can leave it sitting
    # idle-in-transaction, holding a lock TRUNCATE's required ACCESS
    # EXCLUSIVE lock has to wait behind -- forever, since nothing else in
    # this single-threaded request would ever come along to close it.
    # Roll it back first, exactly like the test suite's own
    # `_reset_test_persistence()` already does for the same reason.
    container_session = getattr(getattr(container, "repository_factory", None), "session", None)
    if container_session is not None:
        container_session.rollback()

    tables = _truncate_all_operational_tables()

    # Two projections live outside the truncated SQL tables -- a JSON-file
    # welfare/lifecycle projection and a durable operational-input log.
    # Left alone, either would keep describing animals and inputs that no
    # longer exist after the truncate above (exactly the "absence must
    # never render as good news" trap AA-013 §2.1 warns about, just from
    # the other direction -- stale-but-present data masquerading as
    # current). Clear both so the reset is actually complete.
    if getattr(container, "animal_operational_state_repository", None) is not None:
        container.animal_operational_state_repository.clear()
    if getattr(container, "operational_input_repository", None) is not None:
        container.operational_input_repository.clear()

    # Force a fresh runtime start on next request rather than leaving
    # in-memory state built from the now-truncated data.
    container.started = False
    container.operations = None
    container.dashboard = None

    return {"status": "reset", "tables_cleared": tables}

