from __future__ import annotations

from calendar import month_name
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.auth import get_optional_current_user
from dairyos.api.dependencies import get_container
from dairyos.api.tmr import (
    milk_litres_for_period,
    tmr_feed_cost_for_period,
)
from dairyos.core.time_utils import utcnow
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
from dairyos.finance.classification.transaction_classifier import is_expense

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
    Auto COP from governed operational actuals.

    TMR is Feed cost authority.
    Finance is OPEX authority.
    Milk Production is denominator authority.

    Future dates are never populated from today's live TMR or from
    future-dated Finance/Milk records. OperationalDateAuthority defines
    the final date that can contribute to Auto COP.
    """
    factory = container.repository_factory

    today = OperationalDateAuthority(
        repository_factory=factory,
    ).current_date()

    start = (
        period_start
        or today.replace(day=1)
    )

    requested_end = (
        period_end
        or today
    )

    if requested_end < start:
        raise HTTPException(
            status_code=422,
            detail=(
                "period_end must be on or after "
                "period_start"
            ),
        )

    # Requested period remains visible to the caller, but operational
    # actuals cannot extend beyond the governed operational date.
    effective_end = (
        min(
            requested_end,
            today,
        )
        if start <= today
        else None
    )

    month_row = factory.coml().get_by_month(
        start.replace(day=1)
    )

    # --------------------------------------------------------
    # Milk denominator
    # --------------------------------------------------------

    liters = (
        milk_litres_for_period(
            factory,
            start,
            effective_end,
        )
        if effective_end is not None
        else 0.0
    )

    # --------------------------------------------------------
    # Feed cost
    #
    # tmr_feed_cost_for_period independently enforces the same
    # operational-date boundary and returns zero for future-only
    # periods.
    # --------------------------------------------------------

    feed_basis = tmr_feed_cost_for_period(
        factory,
        start,
        requested_end,
    )

    feed_total = float(
        feed_basis["total_feed_cost"]
    )

    # --------------------------------------------------------
    # Finance operating OPEX
    # --------------------------------------------------------

    opex_total = 0.0
    opex_source = "finance_opex_ledger_empty"

    def _as_date(value):
        if value is None:
            return None

        if (
            hasattr(value, "date")
            and callable(value.date)
        ):
            try:
                return value.date()
            except Exception:
                pass

        if (
            hasattr(value, "year")
            and hasattr(value, "month")
            and hasattr(value, "day")
        ):
            return value

        try:
            from datetime import datetime

            return datetime.fromisoformat(
                str(value).replace(
                    "Z",
                    "+00:00",
                )
            ).date()
        except Exception:
            return None

    OPEX_HINTS = (
        "opex",
        "vet",
        "wage",
        "salary",
        "electric",
        "fuel",
        "maintenance",
        "hygiene",
        "transport",
        "rent",
        "banking",
    )

    try:
        for item in factory.finance().get_all() or []:
            raw_date = (
                getattr(
                    item,
                    "transaction_date",
                    None,
                )
                or getattr(
                    item,
                    "created_at",
                    None,
                )
            )

            transaction_date = _as_date(
                raw_date
            )

            status = str(
                getattr(
                    item,
                    "status",
                    "RECORDED",
                )
                or "RECORDED"
            ).strip().upper()

            if (
                transaction_date is None
                or effective_end is None
                or not (
                    start
                    <= transaction_date
                    <= effective_end
                )
                or not is_expense(item)
                or status == "VOID"
            ):
                continue

            master = str(
                getattr(
                    item,
                    "master_category",
                    None,
                )
                or getattr(
                    item,
                    "category",
                    None,
                )
                or ""
            ).upper()

            sub = str(
                getattr(
                    item,
                    "sub_category",
                    None,
                )
                or getattr(
                    item,
                    "subcategory",
                    None,
                )
                or getattr(
                    item,
                    "category",
                    None,
                )
                or getattr(
                    item,
                    "notes",
                    None,
                )
                or ""
            ).lower()

            amount = float(
                getattr(
                    item,
                    "amount",
                    0.0,
                )
                or 0.0
            )

            if amount <= 0:
                continue

            # Finance Feed purchases establish quantity and rate.
            # They are not consumed-feed COP expense.
            if not (
                master == "OPEX"
                or any(
                    hint in sub
                    for hint in OPEX_HINTS
                )
            ):
                continue

            # Feed-related capital/equipment purchases are visible in
            # Finance and Feed Equipment but are not operating COP.
            if (
                str(
                    getattr(
                        item,
                        "sub_category",
                        "",
                    )
                    or ""
                ).strip()
                == "Equipment Purchase"
            ):
                continue

            opex_total += amount

        if opex_total > 0:
            opex_source = (
                "finance_opex_ledger"
            )

    except Exception:
        # Preserve endpoint availability but make an authority failure
        # explicit in provenance rather than mislabelling it as data.
        opex_total = 0.0
        opex_source = (
            "finance_opex_lookup_failed"
        )

    # --------------------------------------------------------
    # Auto COP
    # --------------------------------------------------------

    feed_per_l = (
        feed_total / liters
        if liters > 0
        else None
    )

    opex_per_l = (
        opex_total / liters
        if liters > 0
        else None
    )

    total_per_l = (
        (feed_total + opex_total)
        / liters
        if liters > 0
        else None
    )

    official = (
        _serialize(month_row)
        if month_row is not None
        else None
    )

    return {
        "data_status": "AUTO_AGGREGATED",
        "period": {
            "start": start.isoformat(),
            "end": requested_end.isoformat(),
        },
        "effective_period": (
            {
                "start": start.isoformat(),
                "end": effective_end.isoformat(),
            }
            if effective_end is not None
            else None
        ),
        "operational_date": (
            today.isoformat()
        ),
        "clamped_to_operational_date": (
            requested_end > today
        ),
        "period_label": (
            f"{start.isoformat()} "
            f"→ {requested_end.isoformat()}"
        ),
        "production": {
            "totalLiters": round(
                liters,
                2,
            ),
            "unit": "liters",
            "basis": "effective_operational_period",
            "source": (
                "milk_production_ledger"
                if liters > 0
                else "milk_production_ledger_empty"
            ),
        },
        "costs": {
            "feed_total": round(
                feed_total,
                2,
            ),
            "opex_total": round(
                opex_total,
                2,
            ),
            "feed_cost_per_liter": (
                round(
                    feed_per_l,
                    4,
                )
                if feed_per_l is not None
                else None
            ),
            "opex_cost_per_liter": (
                round(
                    opex_per_l,
                    4,
                )
                if opex_per_l is not None
                else None
            ),
            "total_coml_per_liter": (
                round(
                    total_per_l,
                    4,
                )
                if total_per_l is not None
                else None
            ),
            "source": (
                "TMR_HERD_COST+FINANCE_OPEX"
            ),
            "feed_source": feed_basis,
            "opex_source": opex_source,
        },
        "feed_cost_per_liter": (
            round(
                feed_per_l,
                4,
            )
            if feed_per_l is not None
            else None
        ),
        "opex_cost_per_liter": (
            round(
                opex_per_l,
                4,
            )
            if opex_per_l is not None
            else None
        ),
        "total_coml_per_liter": (
            round(
                total_per_l,
                4,
            )
            if total_per_l is not None
            else None
        ),
        "official": official,
        "message": (
            "Auto COP uses governed TMR whole-herd feed cost, "
            "authoritative milk production and active Finance OPEX "
            "through the governed operational date. Bulk Feed "
            "purchase spend and Equipment Purchase are not treated "
            "as operating consumption."
        ),
    }
