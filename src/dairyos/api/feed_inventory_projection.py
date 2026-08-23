from __future__ import annotations

from fastapi import APIRouter

from dairyos.api.feed_inventory import _feed_balance, _finance_purchased_quantity
from dairyos.data.repositories.repository_factory import RepositoryFactory


router = APIRouter(prefix="/farm/feed-inventory", tags=["feed-inventory"])


@router.get("/authoritative")
def authoritative_feed_inventory():
    """Return the single backend-owned stock projection used by Feed UI."""
    factory = RepositoryFactory.create()
    try:
        items = []
        for catalog in factory.feed_inventory_items().get_all():
            if not catalog.active:
                continue

            movements = [
                movement
                for movement in factory.inventory().get_all()
                if movement.item == catalog.item
            ]
            purchased = _finance_purchased_quantity(factory, catalog.item, catalog.unit)
            balance = _feed_balance(factory, catalog.item, catalog.unit)
            used = sum(
                abs(float(movement.signed_quantity or 0))
                for movement in movements
                if str(movement.movement_type or "").upper() in {"CONSUMPTION", "WASTAGE"}
                and float(movement.signed_quantity or 0) < 0
            )
            threshold = float(catalog.reorder_level or 0)
            status = "NO_THRESHOLD" if threshold <= 0 else ("LOW" if balance <= threshold else "OK")

            items.append({
                "id": catalog.id,
                "item": catalog.item,
                "category": catalog.category,
                "unit": catalog.unit,
                "location": catalog.location,
                "reorder_level": threshold,
                "active": bool(catalog.active),
                "balance": balance,
                "purchased_from_finance": purchased,
                "used_from_operations": round(used, 3),
                "status": status,
                "transaction_count": len(movements),
                "last_movement_at": max(
                    (m.recorded_at for m in movements if m.recorded_at),
                    default=None,
                ),
            })

        return {
            "data_status": "LIVE_PERSISTED_DATA",
            "frontend_calculation_authority": False,
            "items": items,
            "summary": {
                "active_items": len(items),
                "low_stock_items": sum(1 for item in items if item["status"] == "LOW"),
            },
        }
    finally:
        factory.close()
