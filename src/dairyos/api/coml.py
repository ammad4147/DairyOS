from __future__ import annotations

from calendar import month_name
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.auth import get_optional_current_user
from dairyos.core.time_utils import utcnow
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority

router = APIRouter(prefix="/farm/coml", tags=["COML"])

REMINDER_SETTING_KEY = "coml_reminder_day"
DEFAULT_REMINDER_DAY = 1


class COMLLockRequest(BaseModel):
    month_start: date
    feed_cost_per_liter: float = Field(ge=0)
    opex_cost_per_liter: float = Field(ge=0)
    notes: str | None = None
    updated_by: str = Field(default="UI Operator", min_length=1)


class COMLReminderSettings(BaseModel):
    reminder_day: int = Field(default=DEFAULT_REMINDER_DAY, ge=1, le=28)


def _month_start(value: date) -> date:
    if value.day != 1:
        raise HTTPException(status_code=422, detail="month_start must be the first calendar day of the selected month.")
    return value


def _month_label(value: date) -> str:
    return f"{month_name[value.month]} {value.year}"


def _serialize(row):
    if row is None:
        return None
    return {
        "id": row.id,
        "month_start": row.month_start.isoformat(),
        "month_label": _month_label(row.month_start),
        "feed_cost_per_liter": round(float(row.feed_cost_per_liter), 4),
        "opex_cost_per_liter": round(float(row.opex_cost_per_liter), 4),
        "total_coml_per_liter": round(float(row.total_coml_per_liter), 4),
        "status": row.status,
        "notes": row.notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "locked_at": row.locked_at.isoformat() if row.locked_at else None,
        "updated_by": row.updated_by,
    }


def _current_month_start() -> date:
    return OperationalDateAuthority().current_date().replace(day=1)


def _reminder_status(month_start: date, *, has_official: bool, reminder_day: int, today: date):
    if has_official:
        return "LOCKED"
    if month_start < today.replace(day=1):
        return "OVERDUE"
    if today.day >= reminder_day:
        return "DUE"
    return "UPCOMING"


def _status_payload(month_start: date, row, reminder_day: int):
    today = OperationalDateAuthority().current_date()
    status = _reminder_status(
        month_start,
        has_official=row is not None,
        reminder_day=reminder_day,
        today=today,
    )
    return {
        "month_start": month_start.isoformat(),
        "month_label": _month_label(month_start),
        "has_official": row is not None,
        "record": _serialize(row),
        "reminder_day": reminder_day,
        "reminder_status": status,
        "reminder_due": status in {"DUE", "OVERDUE"},
        "checked_at": utcnow().isoformat(),
    }


@router.get("")
def get_coml(month_start: date | None = None):
    selected = _month_start(month_start) if month_start is not None else _current_month_start()
    rf = RepositoryFactory.create()
    try:
        row = rf.coml().get_by_month(selected)
        reminder_day = int(rf.app_settings().get(REMINDER_SETTING_KEY, DEFAULT_REMINDER_DAY))
        return {"data_status": "LIVE_PERSISTED_DATA", **_status_payload(selected, row, reminder_day)}
    finally:
        rf.close()


@router.get("/current")
def get_current_coml():
    return get_coml(_current_month_start())


@router.get("/history")
def get_coml_history():
    rf = RepositoryFactory.create()
    try:
        return {
            "data_status": "LIVE_PERSISTED_DATA",
            "records": [_serialize(row) for row in rf.coml().get_all()],
        }
    finally:
        rf.close()


@router.post("/lock")
def lock_coml(payload: COMLLockRequest, current_user=Depends(get_optional_current_user)):
    selected = _month_start(payload.month_start)
    feed = round(float(payload.feed_cost_per_liter), 4)
    opex = round(float(payload.opex_cost_per_liter), 4)
    if feed + opex <= 0:
        raise HTTPException(status_code=422, detail="Feed Cost/L + OPEX/L must be greater than zero.")

    rf = RepositoryFactory.create()
    try:
        updated_by = str(current_user["sub"]) if current_user is not None else payload.updated_by.strip()
        row = rf.coml().upsert(
            month_start=selected,
            feed_cost_per_liter=feed,
            opex_cost_per_liter=opex,
            notes=payload.notes,
            updated_by=updated_by or "UI Operator",
        )
        reminder_day = int(rf.app_settings().get(REMINDER_SETTING_KEY, DEFAULT_REMINDER_DAY))
        return {"data_status": "LIVE_PERSISTED_DATA", **_status_payload(selected, row, reminder_day)}
    finally:
        rf.close()


@router.get("/settings")
def get_coml_settings():
    rf = RepositoryFactory.create()
    try:
        reminder_day = int(rf.app_settings().get(REMINDER_SETTING_KEY, DEFAULT_REMINDER_DAY))
        return {"reminder_day": reminder_day, "default_reminder_day": DEFAULT_REMINDER_DAY}
    finally:
        rf.close()


@router.put("/settings")
def set_coml_settings(payload: COMLReminderSettings, current_user=Depends(get_optional_current_user)):
    rf = RepositoryFactory.create()
    try:
        updated_by = str(current_user["sub"]) if current_user is not None else "UI Operator"
        rf.app_settings().set(REMINDER_SETTING_KEY, str(payload.reminder_day), updated_by=updated_by)
        return {"reminder_day": payload.reminder_day}
    finally:
        rf.close()
