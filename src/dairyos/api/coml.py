from __future__ import annotations

from calendar import month_name
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.auth import get_optional_current_user
from dairyos.api.dependencies import get_container
from dairyos.core.time_utils import utcnow
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority

router = APIRouter(prefix="/farm/coml", tags=["COML"])

REMINDER_SETTING_KEY = "coml_reminder_day"
DEFAULT_REMINDER_DAY = 1


class COMLLineItem(BaseModel):
    item: str = Field(min_length=1)
    quantity: Decimal = Field(ge=0)
    unit: str = Field(min_length=1)
    unit_rate: Decimal = Field(ge=0)

    @property
    def total(self) -> Decimal:
        return self.quantity * self.unit_rate


class COMLCalculationRequest(BaseModel):
    period_start: date
    period_end: date
    milk_produced_liters: Decimal = Field(ge=0)
    feed_items: list[COMLLineItem] = Field(default_factory=list)
    operating_items: list[COMLLineItem] = Field(default_factory=list)


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
    status = _reminder_status(month_start, has_official=row is not None, reminder_day=reminder_day, today=today)
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


@router.post("/calculate")
def calculate_coml(payload: COMLCalculationRequest):
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=422, detail="period_end must be on or after period_start")
    liters = Decimal(payload.milk_produced_liters)
    if liters <= 0:
        raise HTTPException(status_code=422, detail="milk_produced_liters must be greater than zero")
    feed_total = sum((item.total for item in payload.feed_items), Decimal("0"))
    opex_total = sum((item.total for item in payload.operating_items), Decimal("0"))
    return {
        "data_status": "CALCULATED_MANUAL_INPUT",
        "period_start": payload.period_start.isoformat(),
        "period_end": payload.period_end.isoformat(),
        "period_days": (payload.period_end - payload.period_start).days + 1,
        "milk_produced_liters": str(liters),
        "feed_total": str(feed_total),
        "operating_total": str(opex_total),
        "feed_cost_per_liter": str(feed_total / liters),
        "opex_cost_per_liter": str(opex_total / liters),
        "total_coml_per_liter": str((feed_total + opex_total) / liters),
        "feed_items": [{**item.model_dump(), "total": str(item.total)} for item in payload.feed_items],
        "operating_items": [{**item.model_dump(), "total": str(item.total)} for item in payload.operating_items],
    }


@router.get("")
def get_coml(month_start: date | None = None, container=Depends(get_container)):
    selected = _month_start(month_start) if month_start is not None else _current_month_start()
    factory = container.repository_factory
    row = factory.coml().get_by_month(selected)
    reminder_day = int(factory.app_settings().get(REMINDER_SETTING_KEY, DEFAULT_REMINDER_DAY))
    return {"data_status": "LIVE_PERSISTED_DATA", **_status_payload(selected, row, reminder_day)}


@router.get("/current")
def get_current_coml(container=Depends(get_container)):
    return get_coml(_current_month_start(), container=container)


@router.get("/history")
def get_coml_history(container=Depends(get_container)):
    factory = container.repository_factory
    return {"data_status": "LIVE_PERSISTED_DATA", "records": [_serialize(row) for row in factory.coml().get_all()]}


@router.post("/lock")
def lock_coml(payload: COMLLockRequest, current_user=Depends(get_optional_current_user), container=Depends(get_container)):
    selected = _month_start(payload.month_start)
    feed = round(float(payload.feed_cost_per_liter), 4)
    opex = round(float(payload.opex_cost_per_liter), 4)
    if feed + opex <= 0:
        raise HTTPException(status_code=422, detail="Feed Cost/L + OPEX/L must be greater than zero.")
    factory = container.repository_factory
    updated_by = str(current_user["sub"]) if current_user is not None else payload.updated_by.strip()
    row = factory.coml().upsert(
        month_start=selected,
        feed_cost_per_liter=feed,
        opex_cost_per_liter=opex,
        notes=payload.notes,
        updated_by=updated_by or "UI Operator",
    )
    reminder_day = int(factory.app_settings().get(REMINDER_SETTING_KEY, DEFAULT_REMINDER_DAY))
    return {"data_status": "LIVE_PERSISTED_DATA", **_status_payload(selected, row, reminder_day)}


@router.get("/settings")
def get_coml_settings(container=Depends(get_container)):
    factory = container.repository_factory
    reminder_day = int(factory.app_settings().get(REMINDER_SETTING_KEY, DEFAULT_REMINDER_DAY))
    return {"reminder_day": reminder_day, "default_reminder_day": DEFAULT_REMINDER_DAY}


@router.put("/settings")
def set_coml_settings(payload: COMLReminderSettings, current_user=Depends(get_optional_current_user), container=Depends(get_container)):
    factory = container.repository_factory
    updated_by = str(current_user["sub"]) if current_user is not None else "UI Operator"
    factory.app_settings().set(REMINDER_SETTING_KEY, str(payload.reminder_day), updated_by=updated_by)
    return {"reminder_day": payload.reminder_day}

@router.get("/integrated")
def get_integrated_coml(
    period_start: date | None = None,
    period_end: date | None = None,
    container=Depends(get_container),
):
    """
    Auto COML for a selected period.
    - Milk liters: best-effort from milk session/yield logs in range
    - Feed + OPEX: best-effort from finance ledger in range
    - Official monthly lock still available via /current
    """
    factory = container.repository_factory
    today = OperationalDateAuthority().current_date()
    start = period_start or _current_month_start()
    end = period_end or today
    if end < start:
        raise HTTPException(status_code=422, detail="period_end must be on or after period_start")

    # Official month record (for reference / priority display when period is that month)
    month_row = factory.coml().get_by_month(start.replace(day=1))

    total_liters = 0.0
    feed_total = 0.0
    opex_total = 0.0
    milk_source = "none"
    ledger_source = "none"

    def _as_date(value):
        if value is None:
            return None
        if hasattr(value, "date") and callable(value.date):
            try:
                return value.date()
            except Exception:
                pass
        if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
            return value
        try:
            from datetime import datetime
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
        except Exception:
            return None

    def _in_range(value) -> bool:
        d = _as_date(value)
        if d is None:
            return False
        return start <= d <= end

    # --- Milk logs ---
    try:
        milk_repo = None
        for name in ("milk_sessions", "milking_sessions", "milk_yields", "milk"):
            getter = getattr(factory, name, None)
            if callable(getter):
                milk_repo = getter()
                break
        records = []
        if milk_repo is not None:
            for method_name in ("list_for_range", "list_between", "get_all", "list", "list_sessions"):
                method = getattr(milk_repo, method_name, None)
                if not callable(method):
                    continue
                try:
                    records = method(start, end) if method_name in {"list_for_range", "list_between"} else method()
                    break
                except TypeError:
                    try:
                        records = method()
                        break
                    except Exception:
                        continue
                except Exception:
                    continue
        for item in records or []:
            get = (lambda k, default=None: item.get(k, default)) if isinstance(item, dict) else (lambda k, default=None: getattr(item, k, default))
            raw_date = get("session_date") or get("date") or get("milking_date") or get("produced_at") or get("timestamp")
            if not _in_range(raw_date):
                continue
            liters = get("total_liters") or get("liters") or get("volume_liters") or get("yield_liters") or get("quantity") or 0
            try:
                total_liters += float(liters or 0)
            except (TypeError, ValueError):
                pass
        milk_source = "milk_logs" if total_liters > 0 else "milk_logs_empty"
    except Exception:
        milk_source = "milk_lookup_failed"

    # --- Finance ledger (feed + opex) ---
    FEED_HINTS = ("feed", "fodder", "silage", "ration", "concentrate", "vanda", "forage")
    OPEX_HINTS = ("opex", "vet", "wage", "salary", "electric", "fuel", "maintenance", "hygiene", "transport", "rent", "banking")
    try:
        fin_repo = None
        for name in ("finance_ledger", "finance", "ledger", "financial_transactions"):
            getter = getattr(factory, name, None)
            if callable(getter):
                fin_repo = getter()
                break
        txns = []
        if fin_repo is not None:
            for method_name in ("list_transactions", "get_all", "list"):
                method = getattr(fin_repo, method_name, None)
                if not callable(method):
                    continue
                try:
                    txns = method()
                    break
                except Exception:
                    continue
        for item in txns or []:
            get = (lambda k, default=None: item.get(k, default)) if isinstance(item, dict) else (lambda k, default=None: getattr(item, k, default))
            raw_date = get("transaction_date") or get("date") or get("posted_at") or get("created_at")
            if not _in_range(raw_date):
                continue
            status = str(get("status") or "").upper()
            if status == "VOID":
                continue
            master = str(get("master_category") or get("category") or "").upper()
            sub = str(get("sub_category") or get("subcategory") or get("description") or "").lower()
            try:
                amount = float(get("amount") or 0)
            except (TypeError, ValueError):
                amount = 0.0
            if amount <= 0:
                continue
            if master == "OPEX" or any(h in sub for h in OPEX_HINTS):
                # classify feed-like opex under feed when obvious
                if any(h in sub for h in FEED_HINTS):
                    feed_total += amount
                else:
                    opex_total += amount
            elif master in {"FEED", "COGS"} or any(h in sub for h in FEED_HINTS):
                feed_total += amount
        ledger_source = "finance_ledger" if (feed_total + opex_total) > 0 else "finance_ledger_empty"
    except Exception:
        ledger_source = "ledger_lookup_failed"

    liters = total_liters if total_liters > 0 else 0.0
    feed_per_l = (feed_total / liters) if liters > 0 else 0.0
    opex_per_l = (opex_total / liters) if liters > 0 else 0.0
    total_per_l = feed_per_l + opex_per_l

    # If period is current month and official exists, expose it (UI may prefer official)
    official = _serialize(month_row) if month_row is not None else None

    return {
        "data_status": "AUTO_AGGREGATED",
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "period_label": f"{start.isoformat()} → {end.isoformat()}",
        "production": {
            "totalLiters": round(liters, 2),
            "unit": "liters",
            "basis": "selected_period",
            "source": milk_source,
        },
        "costs": {
            "feed_total": round(feed_total, 2),
            "opex_total": round(opex_total, 2),
            "feed_cost_per_liter": round(feed_per_l, 4),
            "opex_cost_per_liter": round(opex_per_l, 4),
            "total_coml_per_liter": round(total_per_l, 4),
            "source": ledger_source,
        },
        # flat fields for existing UI
        "feed_cost_per_liter": round(feed_per_l, 4),
        "opex_cost_per_liter": round(opex_per_l, 4),
        "total_coml_per_liter": round(total_per_l, 4),
        "official": official,
        "message": "Auto COML for selected period (milk logs + finance ledger).",
    }
