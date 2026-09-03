from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.dependencies import get_container
from dairyos.finance.classification.transaction_classifier import is_active
from dairyos.core.time_utils import utcnow
from dairyos.data.models.feed_inventory_item import FeedInventoryItem
from dairyos.data.models.feed_ration import FeedRation
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)

router = APIRouter(prefix="/farm/tmr", tags=["tmr"])

TMR_CATALOG_MARKER = "TMR_CATALOG_JSON="
STAGE_GROUP_PREFIX = "TMR_STAGE:"
ENDORSEMENT_GROUP = "TMR_WEEKLY_ENDORSEMENT"

DEFAULT_INGREDIENTS = [
    {
        "catalog_name": "Corn / Maize Silage",
        "display_name": "Silage",
        "dose_unit": "kg",
        "fallback_price_per_kg": 20.0,
    },
    {
        "catalog_name": "Commercial Compound Vanda / Cattle Feed",
        "display_name": "Vanda (Concentrate)",
        "dose_unit": "kg",
        "fallback_price_per_kg": 100.0,
    },
    {
        "catalog_name": "Wheat Straw (Bhoosa)",
        "display_name": "Wheat Straw",
        "dose_unit": "kg",
        "fallback_price_per_kg": 20.0,
    },
    {
        "catalog_name": "Soybean Meal (Hi-Pro)",
        "display_name": "Soybean Meal",
        "dose_unit": "kg",
        "fallback_price_per_kg": 180.0,
    },
    {
        "catalog_name": "Molasses",
        "display_name": "Molasses",
        "dose_unit": "kg",
        "fallback_price_per_kg": 85.0,
    },
    {
        "catalog_name": "Bypass Fat / Rumen-Protected Fat",
        "display_name": "Bypass Fat",
        "dose_unit": "g",
        "fallback_price_per_kg": 480.0,
    },
    {
        "catalog_name": "Dairy Mineral Premix",
        "display_name": "Mineral Mixture",
        "dose_unit": "g",
        "fallback_price_per_kg": 460.0,
    },
    {
        "catalog_name": "Sodium Bicarbonate (Buffer)",
        "display_name": "Meetha Soda",
        "dose_unit": "g",
        "fallback_price_per_kg": 200.0,
    },
    {
        "catalog_name": "Anionic Salts (DCAD)",
        "display_name": "Anionic Salts (DCAD)",
        "dose_unit": "g",
        "fallback_price_per_kg": 350.0,
    },
    {
        "catalog_name": "Toxin Binder",
        "display_name": "Toxin Binder",
        "dose_unit": "g",
        "fallback_price_per_kg": 260.0,
    },
    {
        "catalog_name": "Lysine / Methionine",
        "display_name": "Lysine / Methionine",
        "dose_unit": "g",
        "fallback_price_per_kg": 4000.0,
    },
]

STAGE_LABELS = {
    "early_milking": "Early Lactation",
    "mid_milking": "Mid Lactation",
    "late_milking": "Late Lactation",
    "far_off": "Far-Off Dry",
    "close_up": "Close-Up Dry",
    "heifer_growth": "Growing Heifer",
    "calf_starter": "Calf Starter",
    "bull": "Bull",
}

STAGE_DEFAULT_QUANTITIES = {
    "early_milking": [22, 9.5, 2.5, 2.5, 1, 400, 200, 200, 0, 50, 30],
    "mid_milking": [20, 7, 3.5, 1.5, 0.5, 200, 150, 150, 0, 40, 15],
    "late_milking": [16, 5, 4.5, 1, 0.5, 75, 100, 100, 0, 30, 0],
    "far_off": [10, 2, 6.5, 0, 0, 0, 100, 0, 0, 30, 0],
    "close_up": [12, 3.5, 3.5, 1, 1, 0, 150, 0, 175, 50, 20],
    "heifer_growth": [12, 3, 2.5, 0.5, 0, 0, 100, 50, 0, 30, 0],
    "calf_starter": [4, 2, 0.5, 0, 0, 0, 40, 0, 0, 20, 0],
    # Bull ration approved for the DairyOS TMR tool.
    "bull": [15, 3, 4, 0.5, 0.5, 0, 100, 50, 0, 30, 0],
}

CATEGORY_STAGE_MAP = {
    "Milking": ["early_milking", "mid_milking", "late_milking"],
    "Dry": ["far_off", "close_up"],
    "Heifer": ["heifer_growth"],
    "Female Calf": ["calf_starter"],
    "Male Calf": ["calf_starter"],
    "Bull": ["bull"],
}


class TMRStageIngredient(BaseModel):
    catalog_name: str = Field(min_length=1)
    quantity: float = Field(ge=0)
    dose_unit: str = Field(default="kg")
    fallback_price_per_kg: float = Field(default=0, ge=0)


class TMRStageUpdate(BaseModel):
    stage: str = Field(min_length=1)
    ingredients: list[TMRStageIngredient]
    operator: str = Field(default="UI Operator", min_length=1)


class TMRIngredientCreate(BaseModel):
    name: str = Field(min_length=1)
    display_name: str | None = None
    dose_unit: str = Field(default="kg")
    fallback_price_per_kg: float = Field(default=0, ge=0)


class TMREndorsement(BaseModel):
    reviewer: str = Field(min_length=1)
    notes: str | None = None


def tmr_default_catalog_names() -> list[str]:
    return [str(row["catalog_name"]) for row in DEFAULT_INGREDIENTS]


def _catalog_metadata_from_notes(notes: str | None) -> dict | None:
    for line in reversed(str(notes or "").splitlines()):
        if not line.startswith(TMR_CATALOG_MARKER):
            continue
        try:
            value = json.loads(line[len(TMR_CATALOG_MARKER):])
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None
    return None


def _with_catalog_metadata(existing_notes: str | None, metadata: dict) -> str:
    kept = [
        line
        for line in str(existing_notes or "").splitlines()
        if not line.startswith(TMR_CATALOG_MARKER)
    ]
    kept.append(
        TMR_CATALOG_MARKER
        + json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    )
    return "\n".join(line for line in kept if line).strip()


def is_tmr_catalog_row(row) -> bool:
    return _catalog_metadata_from_notes(getattr(row, "notes", None)) is not None


def _custom_ingredient_definitions(factory) -> list[dict]:
    result: list[dict] = []
    defaults = set(tmr_default_catalog_names())
    for row in factory.feed_inventory_items().get_all():
        if not bool(getattr(row, "active", True)):
            continue
        metadata = _catalog_metadata_from_notes(getattr(row, "notes", None))
        if metadata is None:
            continue
        name = str(getattr(row, "item", "") or "").strip()
        if not name or name in defaults:
            continue
        dose_unit = str(metadata.get("dose_unit") or "kg").strip().lower()
        if dose_unit not in {"kg", "g"}:
            dose_unit = "kg"
        result.append(
            {
                "catalog_name": name,
                "display_name": str(metadata.get("display_name") or name),
                "dose_unit": dose_unit,
                "fallback_price_per_kg": float(
                    metadata.get("fallback_price_per_kg") or 0.0
                ),
            }
        )
    result.sort(key=lambda row: row["display_name"].lower())
    return result


def _ingredient_definitions(factory) -> list[dict]:
    return [
        *[dict(item) for item in DEFAULT_INGREDIENTS],
        *_custom_ingredient_definitions(factory),
    ]


def _default_stage_ingredients(factory, stage: str) -> list[dict]:
    definitions = _ingredient_definitions(factory)
    quantities = STAGE_DEFAULT_QUANTITIES[stage]
    result: list[dict] = []
    for index, definition in enumerate(definitions):
        quantity = quantities[index] if index < len(quantities) else 0.0
        result.append(
            {
                **definition,
                "quantity": float(quantity),
            }
        )
    return result


def _saved_stage_ingredients(factory, stage: str) -> list[dict] | None:
    group = f"{STAGE_GROUP_PREFIX}{stage}"
    rows = factory.feed_rations().get_active_for_group(group)
    if not rows:
        return None
    for row in rows:
        try:
            payload = json.loads(row.ingredients_json)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(payload, list):
            return payload
    return None


def _stage_ingredients(factory, stage: str) -> list[dict]:
    definitions = _ingredient_definitions(factory)
    saved = _saved_stage_ingredients(factory, stage)
    saved_by_name = {
        str(row.get("catalog_name") or "").strip(): row
        for row in (saved or [])
        if isinstance(row, dict)
    }
    defaults = _default_stage_ingredients(factory, stage)
    defaults_by_name = {row["catalog_name"]: row for row in defaults}

    result: list[dict] = []
    for definition in definitions:
        name = definition["catalog_name"]
        base = defaults_by_name[name]
        prior = saved_by_name.get(name, {})
        dose_unit = str(
            prior.get("dose_unit")
            or definition["dose_unit"]
        ).strip().lower()
        if dose_unit not in {"kg", "g"}:
            dose_unit = definition["dose_unit"]
        result.append(
            {
                **definition,
                "quantity": float(prior.get("quantity", base["quantity"]) or 0.0),
                "dose_unit": dose_unit,
                "fallback_price_per_kg": float(
                    prior.get(
                        "fallback_price_per_kg",
                        definition["fallback_price_per_kg"],
                    )
                    or 0.0
                ),
            }
        )
    return result


def _finance_feed_item_name(row) -> str | None:
    if str(getattr(row, "master_category", "") or "").strip().upper() != "FEED":
        return None
    sub = str(getattr(row, "sub_category", "") or "").strip()
    if not sub:
        return None
    if sub == "Other":
        custom = str(
            getattr(row, "custom_specification", "") or ""
        ).strip()
        return custom or None
    return sub


def _finance_price_authority(factory) -> dict[str, dict]:
    authority: dict[str, dict] = {}
    for row in factory.finance().get_all() or []:
        if not is_active(row):
            continue
        transaction_type = str(
            getattr(row, "transaction_type", "") or ""
        ).strip().upper()
        if transaction_type not in {"EXPENSE", "PAYMENT", "PURCHASE"}:
            continue
        name = _finance_feed_item_name(row)
        if not name:
            continue
        unit = str(getattr(row, "unit", "") or "").strip().lower()
        if unit and unit not in {"kg", "kgs", "kilogram", "kilograms"}:
            continue
        rate = float(getattr(row, "unit_rate", 0.0) or 0.0)
        if rate <= 0:
            continue
        transaction_date = getattr(row, "transaction_date", None)
        key = (
            str(transaction_date or ""),
            int(getattr(row, "id", 0) or 0),
        )
        existing = authority.get(name)
        if existing is not None and existing["sort_key"] >= key:
            continue
        authority[name] = {
            "sort_key": key,
            "price_per_kg": rate,
            "transaction_id": getattr(row, "id", None),
            "purchase_date": (
                _as_date(transaction_date).isoformat()
                if _as_date(transaction_date) is not None
                else None
            ),
        }
    return authority


def _priced_stage(
    factory,
    stage: str,
    price_authority: dict[str, dict],
) -> dict:
    rows = []
    total = 0.0
    total_kg = 0.0

    for ingredient in _stage_ingredients(factory, stage):
        name = ingredient["catalog_name"]
        finance = price_authority.get(name)
        fallback_rate = float(
            ingredient["fallback_price_per_kg"] or 0.0
        )
        rate = (
            float(finance["price_per_kg"])
            if finance is not None
            else fallback_rate
        )
        quantity = float(ingredient["quantity"] or 0.0)
        dose_unit = ingredient["dose_unit"]
        quantity_kg = (
            quantity / 1000.0
            if dose_unit == "g"
            else quantity
        )
        line_cost = quantity_kg * rate
        total += line_cost
        total_kg += quantity_kg
        rows.append(
            {
                **ingredient,
                "price_per_kg": round(rate, 4),
                "price_source": (
                    "FINANCE"
                    if finance is not None
                    else "MANUAL_FALLBACK"
                ),
                "finance_transaction_id": (
                    finance["transaction_id"]
                    if finance is not None
                    else None
                ),
                "finance_purchase_date": (
                    finance["purchase_date"]
                    if finance is not None
                    else None
                ),
                "cost_per_head_day": round(line_cost, 4),
            }
        )

    return {
        "key": stage,
        "label": STAGE_LABELS[stage],
        "ingredients": rows,
        "ration_kg_per_head_day": round(total_kg, 4),
        "cost_per_head_day": round(total, 4),
        "source": "GOVERNED_TMR",
    }


def _normalize_herd_category(animal) -> str | None:
    raw = str(getattr(animal, "animal_type", "") or "").strip().upper()
    normalized = raw.replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.split())

    aliases = {
        "MILKING": "Milking",
        "MILKING COW": "Milking",
        "MILKING COWS": "Milking",
        "DRY": "Dry",
        "DRY COW": "Dry",
        "DRY COWS": "Dry",
        "HEIFER": "Heifer",
        "HEIFERS": "Heifer",
        "FEMALE CALF": "Female Calf",
        "FEMALE CALVES": "Female Calf",
        "MALE CALF": "Male Calf",
        "MALE CALVES": "Male Calf",
        "BULL": "Bull",
        "BULLS": "Bull",
    }
    category = aliases.get(normalized)
    if category is not None:
        return category

    if bool(getattr(animal, "is_currently_milking", False)):
        return "Milking"
    return None


def _active_herd_counts(factory) -> dict[str, int]:
    counts = {category: 0 for category in CATEGORY_STAGE_MAP}
    inactive_statuses = {
        "SOLD",
        "DECEASED",
        "DEAD",
        "DISPOSED",
        "INACTIVE",
        "VOID",
    }
    for animal in factory.animal().active_animals():
        status = str(getattr(animal, "status", "ACTIVE") or "ACTIVE").upper()
        if status in inactive_statuses:
            continue
        category = _normalize_herd_category(animal)
        if category in counts:
            counts[category] += 1
    return counts


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        ).date()
    except (TypeError, ValueError):
        return None


def milk_litres_for_period(factory, start: date, end: date) -> float:
    total = 0.0
    for item in factory.milk().get_all() or []:
        status = str(
            getattr(item, "status", "RECORDED") or "RECORDED"
        ).upper()
        if status in {"VOID", "NOT_MILKED"}:
            continue
        raw_date = (
            getattr(item, "production_date", None)
            or getattr(item, "recorded_at", None)
        )
        production_date = _as_date(raw_date)
        if production_date is None or not (start <= production_date <= end):
            continue
        total_yield = getattr(item, "total_yield", None)
        if total_yield is None:
            total_yield = sum(
                float(value)
                for value in (
                    getattr(item, "morning_yield", None),
                    getattr(item, "afternoon_yield", None),
                    getattr(item, "evening_yield", None),
                )
                if value is not None
            )
        total += float(total_yield or 0.0)
    return round(total, 4)


def _week_bounds(day: date) -> tuple[date, date]:
    start = day - timedelta(days=day.weekday())
    return start, start + timedelta(days=6)


def _endorsement_snapshots(factory) -> list[dict]:
    snapshots: list[dict] = []
    for row in factory.feed_rations().get_active_for_group(ENDORSEMENT_GROUP):
        try:
            snapshot = json.loads(row.ingredients_json)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(snapshot, dict):
            continue
        snapshot = {
            **snapshot,
            "record_id": getattr(row, "id", None),
            "reviewer": getattr(row, "operator", None),
            "recorded_at": (
                row.created_at.isoformat()
                if getattr(row, "created_at", None)
                else None
            ),
        }
        snapshots.append(snapshot)
    return snapshots


def _weekly_review(factory, today: date) -> dict:
    week_start, week_end = _week_bounds(today)
    current = [
        row
        for row in _endorsement_snapshots(factory)
        if row.get("week_start") == week_start.isoformat()
    ]
    latest = current[0] if current else None
    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "status": "ENDORSED" if latest else "DUE",
        "advisory": (
            "TMR reviewed and endorsed for the current herd week."
            if latest
            else "Vet review due: review/update the whole-herd TMR and endorse it for this week."
        ),
        "endorsement": latest,
    }


def _category_costs(stages: dict, counts: dict[str, int]) -> list[dict]:
    result = []
    for category, stage_keys in CATEGORY_STAGE_MAP.items():
        values = [
            float(stages[key]["cost_per_head_day"])
            for key in stage_keys
        ]
        head_cost = sum(values) / len(values) if values else 0.0
        count = int(counts.get(category, 0))
        result.append(
            {
                "category": category,
                "stage_keys": stage_keys,
                "animal_count": count,
                "cost_per_head_day": round(head_cost, 4),
                "category_cost_per_day": round(head_cost * count, 4),
            }
        )
    return result


def governed_tmr_catalog_names(factory) -> list[str]:
    """
    Return the canonical ingredient identities used by governed TMR.

    Finance FEED purchases consume this exact authority so purchase
    quantities, rates, Feed Storage and TMR pricing cannot diverge by
    ingredient name.
    """
    return list(
        dict.fromkeys(
            str(
                row.get("catalog_name") or ""
            ).strip()
            for row in _ingredient_definitions(factory)
            if str(
                row.get("catalog_name") or ""
            ).strip()
        )
    )


def build_live_tmr_summary(factory, *, include_weekly_review: bool = True) -> dict:
    operational_date = OperationalDateAuthority(
        repository_factory=factory,
    ).current_date()
    price_authority = _finance_price_authority(factory)
    stages = {
        key: _priced_stage(factory, key, price_authority)
        for key in STAGE_LABELS
    }
    counts = _active_herd_counts(factory)
    categories = _category_costs(stages, counts)
    total_daily = sum(
        float(row["category_cost_per_day"])
        for row in categories
    )
    milk_today = milk_litres_for_period(
        factory,
        operational_date,
        operational_date,
    )
    feed_per_litre = (
        total_daily / milk_today
        if milk_today > 0
        else None
    )
    payload = {
        "data_status": "LIVE_PERSISTED_TMR",
        "operational_date": operational_date.isoformat(),
        "ingredients": _ingredient_definitions(factory),
        "stages": stages,
        "categories": categories,
        "herd_counts": counts,
        "total_herd_feed_cost_per_day": round(total_daily, 4),
        "milk_production_today_liters": round(milk_today, 4),
        "feed_cost_per_litre_today": (
            round(feed_per_litre, 4)
            if feed_per_litre is not None
            else None
        ),
        "feed_cost_basis": "TMR_RATION_X_ACTIVE_HERD",
    }
    if include_weekly_review:
        payload["weekly_review"] = _weekly_review(factory, operational_date)
    return payload


def tmr_feed_cost_for_period(factory, start: date, end: date) -> dict:
    if end < start:
        raise ValueError("end must be on or after start")

    requested_end = end

    today = OperationalDateAuthority(
        repository_factory=factory,
    ).current_date()

    # Auto TMR cost is operational fact, not a forecast.
    # A future-only request therefore has no authoritative feed cost.
    if start > today:
        return {
            "total_feed_cost": 0.0,
            "daily": [],
            "endorsed_days": 0,
            "fallback_days": 0,
            "source": "TMR_HERD_COST",
            "requested_period": {
                "start": start.isoformat(),
                "end": requested_end.isoformat(),
            },
            "effective_period": None,
            "operational_date": today.isoformat(),
            "clamped_to_operational_date": True,
        }

    effective_end = min(
        requested_end,
        today,
    )

    live = build_live_tmr_summary(factory, include_weekly_review=False)
    live_daily = float(live["total_herd_feed_cost_per_day"])
    endorsements = _endorsement_snapshots(factory)

    by_week: dict[str, dict] = {}
    for snapshot in reversed(endorsements):
        week_start = str(snapshot.get("week_start") or "")
        if week_start:
            by_week[week_start] = snapshot

    day = start
    total = 0.0
    daily_rows = []
    endorsed_days = 0
    fallback_days = 0

    while day <= effective_end:
        week_start, _ = _week_bounds(day)
        snapshot = by_week.get(week_start.isoformat())

        if day == today:
            amount = live_daily
            basis = "LIVE_TMR"
        elif snapshot is not None:
            amount = float(
                snapshot.get("total_herd_feed_cost_per_day") or 0.0
            )
            basis = "WEEKLY_VET_ENDORSED_TMR"
            endorsed_days += 1
        else:
            amount = live_daily
            basis = "UNENDORSED_LIVE_TMR_FALLBACK"
            fallback_days += 1

        total += amount
        daily_rows.append(
            {
                "date": day.isoformat(),
                "feed_cost": round(amount, 4),
                "basis": basis,
                "week_start": week_start.isoformat(),
            }
        )
        day += timedelta(days=1)

    return {
        "total_feed_cost": round(total, 4),
        "daily": daily_rows,
        "endorsed_days": endorsed_days,
        "fallback_days": fallback_days,
        "source": "TMR_HERD_COST",
        "requested_period": {
            "start": start.isoformat(),
            "end": requested_end.isoformat(),
        },
        "effective_period": {
            "start": start.isoformat(),
            "end": effective_end.isoformat(),
        },
        "operational_date": today.isoformat(),
        "clamped_to_operational_date": (
            requested_end > today
        ),
    }


@router.get("")
def get_tmr(container=Depends(get_container)):
    factory = container.repository_factory
    return build_live_tmr_summary(factory)


@router.post("/stages")
def save_tmr_stage(
    payload: TMRStageUpdate,
    container=Depends(get_container),
):
    stage = payload.stage.strip()
    if stage not in STAGE_LABELS:
        raise HTTPException(status_code=422, detail="Unknown TMR stage.")

    allowed = {
        row["catalog_name"]
        for row in _ingredient_definitions(container.repository_factory)
    }
    normalized = []
    for row in payload.ingredients:
        name = row.catalog_name.strip()
        unit = row.dose_unit.strip().lower()
        if name not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown TMR ingredient: {name}",
            )
        if unit not in {"kg", "g"}:
            raise HTTPException(
                status_code=422,
                detail="dose_unit must be kg or g.",
            )
        normalized.append(
            {
                "catalog_name": name,
                "quantity": float(row.quantity),
                "dose_unit": unit,
                "fallback_price_per_kg": float(
                    row.fallback_price_per_kg
                ),
            }
        )

    factory = container.repository_factory
    record = FeedRation(
        name=f"TMR {STAGE_LABELS[stage]}",
        animal_group=f"{STAGE_GROUP_PREFIX}{stage}",
        ingredients_json=json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
        ),
        target_dmi_kg=None,
        dry_matter_pct=None,
        crude_protein_pct=None,
        ndf_pct=None,
        energy_mcal_kg=None,
        cost_per_kg=None,
        effective_date=utcnow().isoformat(),
        operator=payload.operator.strip(),
    )
    factory.feed_rations().add(record)
    return {
        "saved": True,
        "record_id": record.id,
        "stage": stage,
        "summary": build_live_tmr_summary(factory),
    }


@router.post("/ingredients")
def add_tmr_ingredient(
    payload: TMRIngredientCreate,
    container=Depends(get_container),
):
    factory = container.repository_factory
    name = payload.name.strip()
    display_name = (payload.display_name or name).strip()
    dose_unit = payload.dose_unit.strip().lower()
    if dose_unit not in {"kg", "g"}:
        raise HTTPException(
            status_code=422,
            detail="dose_unit must be kg or g.",
        )

    metadata = {
        "display_name": display_name,
        "dose_unit": dose_unit,
        "fallback_price_per_kg": float(
            payload.fallback_price_per_kg
        ),
    }

    existing = factory.feed_inventory_items().get_by_item(name)
    if existing is None:
        existing = FeedInventoryItem(
            item=name,
            category="FEED",
            unit="kg",
            reorder_level=0,
            active=True,
            notes=_with_catalog_metadata(None, metadata),
        )
    else:
        existing.active = True
        existing.notes = _with_catalog_metadata(
            getattr(existing, "notes", None),
            metadata,
        )

    factory.session.add(existing)
    factory.session.commit()
    factory.session.refresh(existing)

    return {
        "data_status": "LIVE_PERSISTED_DATA",
        "id": existing.id,
        "catalog_name": existing.item,
        "display_name": display_name,
        "purchase_unit": existing.unit,
        "dose_unit": dose_unit,
        "fallback_price_per_kg": float(
            payload.fallback_price_per_kg
        ),
    }


@router.post("/endorse")
def endorse_weekly_tmr(
    payload: TMREndorsement,
    container=Depends(get_container),
):
    factory = container.repository_factory
    today = OperationalDateAuthority(
        repository_factory=factory,
    ).current_date()
    week_start, week_end = _week_bounds(today)
    summary = build_live_tmr_summary(
        factory,
        include_weekly_review=False,
    )

    snapshot = {
        "kind": "TMR_WEEKLY_ENDORSEMENT",
        "status": "ENDORSED",
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "reviewed_on": today.isoformat(),
        "reviewed_at": utcnow().isoformat(),
        "reviewer": payload.reviewer.strip(),
        "notes": payload.notes,
        "categories": summary["categories"],
        "herd_counts": summary["herd_counts"],
        "stages": summary["stages"],
        "total_herd_feed_cost_per_day": summary[
            "total_herd_feed_cost_per_day"
        ],
        "milk_production_today_liters": summary[
            "milk_production_today_liters"
        ],
        "feed_cost_per_litre_today": summary[
            "feed_cost_per_litre_today"
        ],
    }

    record = FeedRation(
        name=f"TMR Weekly Herd Review {week_start.isoformat()}",
        animal_group=ENDORSEMENT_GROUP,
        ingredients_json=json.dumps(
            snapshot,
            sort_keys=True,
            separators=(",", ":"),
        ),
        target_dmi_kg=None,
        dry_matter_pct=None,
        crude_protein_pct=None,
        ndf_pct=None,
        energy_mcal_kg=None,
        cost_per_kg=None,
        effective_date=utcnow().isoformat(),
        operator=payload.reviewer.strip(),
    )
    factory.feed_rations().add(record)

    return {
        "data_status": "LIVE_PERSISTED_DATA",
        "record_id": record.id,
        "weekly_review": _weekly_review(factory, today),
        "summary": build_live_tmr_summary(factory),
    }
