from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from dairyos.api.dependencies import get_container
from dairyos.finance.clinical_inventory import record_clinical_receipt

router = APIRouter(prefix="/farm/clinical-inventory", tags=["Clinical Inventory"])


class ClinicalReceiptRequest(BaseModel):
    item: str
    quantity: float = Field(gt=0)
    unit: str
    supplier: str | None = None
    source_id: str | None = None
    notes: str | None = None
    recorded_by: str = "Operator UI"


@router.post("/receipts")
def record_receipt(payload: ClinicalReceiptRequest, container=Depends(get_container)) -> dict[str, Any]:  # noqa: B008
    row = record_clinical_receipt(container, **payload.model_dump())
    return {"id": row.id, "item": row.item, "quantity": row.quantity, "unit": row.unit, "movement_type": row.movement_type}


@router.get("/balance")
def clinical_balance(container=Depends(get_container)) -> list[dict[str, Any]]:  # noqa: B008
    rows = container.repository_factory.inventory().get_all()
    clinical_types = {"CLINICAL_RECEIPT", "TREATMENT_CONSUMPTION", "VACCINATION_CONSUMPTION"}
    items = sorted({row.item for row in rows if row.source_type in clinical_types})
    balances = container.repository_factory.inventory().balance_by_item()
    return [{"item": item, **balances[item]} for item in items if item in balances]
