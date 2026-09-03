from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.dependencies import get_container
from dairyos.api.finance_ledger import (
    EQUIPMENT_PURCHASE_ITEM,
)
from dairyos.data.models.feed_ration import FeedRation


router = APIRouter(
    prefix="/farm/feed-equipment",
    tags=["feed-equipment"],
)


STATUS_GROUP_PREFIX = "FEED_EQUIPMENT_STATUS:"


class FeedEquipmentStatusUpdate(BaseModel):
    status: str = Field(min_length=1)
    operator: str = Field(
        default="UI Operator",
        min_length=1,
    )


def _active_finance_row(row) -> bool:
    status = str(
        getattr(row, "status", "") or ""
    ).strip().upper()

    return status not in {
        "VOID",
        "CANCELLED",
        "DELETED",
    }


def _is_equipment_purchase(row) -> bool:
    transaction_type = str(
        getattr(row, "transaction_type", "") or ""
    ).strip().upper()

    return (
        _active_finance_row(row)
        and transaction_type
        in {
            "EXPENSE",
            "PAYMENT",
            "PURCHASE",
        }
        and str(
            getattr(row, "master_category", "")
            or ""
        ).strip().upper()
        == "OPEX"
        and str(
            getattr(row, "sub_category", "")
            or ""
        ).strip()
        == EQUIPMENT_PURCHASE_ITEM
        and bool(
            str(
                getattr(
                    row,
                    "custom_specification",
                    "",
                )
                or ""
            ).strip()
        )
    )


def _status_group(finance_id: int) -> str:
    return (
        f"{STATUS_GROUP_PREFIX}"
        f"{int(finance_id)}"
    )


def _latest_manual_status(
    factory,
    finance_id: int,
) -> dict | None:
    rows = factory.feed_rations().get_active_for_group(
        _status_group(finance_id)
    )

    for row in rows:
        try:
            payload = json.loads(
                row.ingredients_json
            )
        except (
            TypeError,
            json.JSONDecodeError,
        ):
            continue

        if not isinstance(payload, dict):
            continue

        status = str(
            payload.get("status") or ""
        ).strip().upper()

        if status not in {
            "OPERATIONAL",
            "NON_OPERATIONAL",
        }:
            continue

        return {
            **payload,
            "record_id": getattr(
                row,
                "id",
                None,
            ),
            "operator": getattr(
                row,
                "operator",
                None,
            ),
            "recorded_at": (
                row.created_at.isoformat()
                if getattr(
                    row,
                    "created_at",
                    None,
                )
                else None
            ),
        }

    return None


def _finance_date(row) -> str | None:
    value = getattr(
        row,
        "transaction_date",
        None,
    )

    if value is None:
        return None

    if hasattr(value, "date"):
        return value.date().isoformat()

    return str(value)[:10]


def _equipment_row(
    factory,
    row,
) -> dict:
    manual = _latest_manual_status(
        factory,
        int(row.id),
    )

    return {
        "finance_transaction_id": row.id,
        "equipment_name": str(
            row.custom_specification
            or ""
        ).strip(),
        "purchase_date": _finance_date(
            row
        ),
        "supplier": (
            getattr(
                row,
                "counterparty",
                None,
            )
            or getattr(
                row,
                "vendor_name",
                None,
            )
        ),
        "finance_reference": getattr(
            row,
            "reference",
            None,
        ),
        "quantity": getattr(
            row,
            "quantity",
            None,
        ),
        "unit": getattr(
            row,
            "unit",
            None,
        ),
        "unit_rate": getattr(
            row,
            "unit_rate",
            None,
        ),
        "amount": float(
            getattr(
                row,
                "amount",
                0.0,
            )
            or 0.0
        ),
        "finance_status": getattr(
            row,
            "status",
            None,
        ),

        # No inferred/automatic equipment status.
        "status": (
            manual["status"]
            if manual is not None
            else "NOT_SET"
        ),

        "status_source": (
            "MANUAL"
            if manual is not None
            else "UNSET"
        ),

        "status_operator": (
            manual.get("operator")
            if manual is not None
            else None
        ),

        "status_recorded_at": (
            manual.get("recorded_at")
            if manual is not None
            else None
        ),
    }


@router.get("")
def feed_equipment_list(
    container=Depends(get_container),
):
    factory = container.repository_factory

    purchases = [
        row
        for row in factory.finance().get_all()
        or []
        if _is_equipment_purchase(row)
    ]

    purchases.sort(
        key=lambda row: (
            str(
                getattr(
                    row,
                    "transaction_date",
                    "",
                )
                or ""
            ),
            int(
                getattr(
                    row,
                    "id",
                    0,
                )
                or 0
            ),
        ),
        reverse=True,
    )

    rows = [
        _equipment_row(
            factory,
            row,
        )
        for row in purchases
    ]

    return {
        "data_status": (
            "LIVE_PERSISTED_DATA"
        ),
        "source": (
            "FINANCE_EQUIPMENT_PURCHASES"
        ),
        "status_authority": (
            "MANUAL_ONLY"
        ),
        "equipment": rows,
        "count": len(rows),
    }


@router.post(
    "/{finance_transaction_id}/status"
)
def set_feed_equipment_status(
    finance_transaction_id: int,
    payload: FeedEquipmentStatusUpdate,
    container=Depends(get_container),
):
    factory = container.repository_factory

    finance_row = factory.finance().get_by_id(
        finance_transaction_id
    )

    if (
        finance_row is None
        or not _is_equipment_purchase(
            finance_row
        )
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "Active Finance Equipment "
                "Purchase was not found."
            ),
        )

    status = payload.status.strip().upper()

    if status not in {
        "OPERATIONAL",
        "NON_OPERATIONAL",
    }:
        raise HTTPException(
            status_code=422,
            detail=(
                "status must be OPERATIONAL "
                "or NON_OPERATIONAL."
            ),
        )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    snapshot = {
        "kind": (
            "FEED_EQUIPMENT_MANUAL_STATUS"
        ),
        "finance_transaction_id": (
            finance_transaction_id
        ),
        "equipment_name": str(
            finance_row.custom_specification
            or ""
        ).strip(),
        "status": status,
        "recorded_at": now,
    }

    record = FeedRation(
        name=(
            "Feed Equipment Status "
            f"#{finance_transaction_id}"
        ),
        animal_group=_status_group(
            finance_transaction_id
        ),
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
        effective_date=now,
        operator=payload.operator.strip(),
    )

    factory.feed_rations().add(
        record
    )

    return {
        "data_status": (
            "LIVE_PERSISTED_DATA"
        ),
        "source": (
            "MANUAL_EQUIPMENT_STATUS"
        ),
        "equipment": _equipment_row(
            factory,
            finance_row,
        ),
    }
