from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.api.feed_inventory import (
    _feed_raw_balance,
    _finance_purchased_quantity,
    _latest_finance_purchase,
    _latest_finance_unit_rate,
    _storage_movement_breakdown,
)


router = APIRouter(
    prefix="/farm/feed-inventory",
    tags=["feed-inventory"],
)


@router.get("/authoritative")
def authoritative_feed_inventory(
    container=Depends(get_container),
):
    """
    Single backend-owned Feed Storage projection.

    Finance = purchase authority.
    TMR = automatic consumption authority.
    ADJUSTMENT manual override = physical stock correction only.
    """
    factory = getattr(
        container,
        "repository_factory",
        None,
    )

    if factory is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Canonical repository factory "
                "is not available"
            ),
        )

    # Read-only projection. Automatic TMR storage reconciliation is
    # owned by the DairyOS runtime scheduler, not by this GET request.
    automatic_sync = {
        "authority": "RUNTIME_SCHEDULER",
        "write_on_get": False,
    }

    all_movements = list(
        factory.inventory().get_all()
    )

    items = []

    for catalog in factory.feed_inventory_items().get_all():
        if not catalog.active:
            continue

        movements = [
            movement
            for movement in all_movements
            if movement.item == catalog.item
        ]

        purchased = _finance_purchased_quantity(
            factory,
            catalog.item,
            catalog.unit,
        )

        latest_purchase = _latest_finance_purchase(
            factory,
            catalog.item,
            catalog.unit,
        )

        latest_unit_rate = _latest_finance_unit_rate(
            factory,
            catalog.item,
            catalog.unit,
        )

        raw_balance = _feed_raw_balance(
            factory,
            catalog.item,
            catalog.unit,
        )

        balance = max(0.0, raw_balance)
        shortage = max(0.0, -raw_balance)

        movement_breakdown = (
            _storage_movement_breakdown(
                movements
            )
        )

        threshold = float(
            catalog.reorder_level or 0
        )

        status = (
            "SHORTAGE"
            if shortage > 0
            else (
                "NO_THRESHOLD"
                if threshold <= 0
                else (
                    "LOW"
                    if balance <= threshold
                    else "OK"
                )
            )
        )

        items.append(
            {
                "id": catalog.id,
                "item": catalog.item,
                "category": catalog.category,
                "unit": catalog.unit,
                "location": catalog.location,
                "reorder_level": threshold,
                "active": bool(catalog.active),

                "purchased_from_finance": round(
                    purchased,
                    3,
                ),

                "auto_consumed_from_tmr": (
                    movement_breakdown[
                        "auto_consumed_from_tmr"
                    ]
                ),

                "manual_override_net": (
                    movement_breakdown[
                        "manual_override_net"
                    ]
                ),

                # Compatibility/audit only. Direct manual usage
                # is no longer a current authority.
                "legacy_manual_usage": (
                    movement_breakdown[
                        "legacy_manual_usage"
                    ]
                ),

                "used_from_operations": (
                    movement_breakdown[
                        "auto_consumed_from_tmr"
                    ]
                ),

                "projected_balance": round(
                    raw_balance,
                    3,
                ),

                "balance": round(
                    balance,
                    3,
                ),

                "shortage": round(
                    shortage,
                    3,
                ),

                "latest_finance_unit_rate": (
                    latest_unit_rate
                ),

                "latest_finance_transaction_id": (
                    latest_purchase.id
                    if latest_purchase is not None
                    else None
                ),

                "latest_finance_purchase_date": (
                    latest_purchase.transaction_date.date().isoformat()
                    if (
                        latest_purchase is not None
                        and latest_purchase.transaction_date is not None
                    )
                    else None
                ),

                "status": status,
                "transaction_count": len(
                    movements
                ),

                "last_movement_at": max(
                    (
                        movement.recorded_at
                        for movement in movements
                        if movement.recorded_at
                    ),
                    default=None,
                ),
            }
        )

    return {
        "data_status": "LIVE_PERSISTED_DATA",
        "frontend_calculation_authority": False,
        "purchase_authority": "FINANCE_FEED",
        "consumption_authority": (
            "GOVERNED_TMR_X_ACTIVE_HERD"
        ),
        "manual_override_authority": (
            "SIGNED_PHYSICAL_STOCK_ADJUSTMENT"
        ),
        "automatic_consumption_sync": automatic_sync,
        "items": items,
        "summary": {
            "active_items": len(items),
            "low_stock_items": sum(
                1
                for item in items
                if item["status"] == "LOW"
            ),
            "shortage_items": sum(
                1
                for item in items
                if item["status"] == "SHORTAGE"
            ),
        },
    }
