from dataclasses import dataclass

import pytest

from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
)


@dataclass
class Disposition:
    id: int
    quantity_litres: float
    disposition_type: str
    status: str = "RECORDED"


def basis(total=100.0, withdrawal=20.0):
    return {
        "complete": True,
        "daily_total": total,
        "saleable_litres": total - withdrawal,
        "withdrawal_litres": withdrawal,
    }


def test_ordinary_disposition_cannot_consume_withdrawal_litres():
    existing = [Disposition(1, 70.0, "SOLD")]
    with pytest.raises(ValueError, match="saleable production"):
        MilkReconciliationService.validate_disposition_quantity(
            production_basis=basis(),
            dispositions=existing,
            disposition_type="SOLD",
            quantity_litres=11.0,
        )


def test_withdrawal_disposition_uses_withdrawal_pool_only():
    existing = [Disposition(1, 10.0, "WITHDRAWAL")]
    MilkReconciliationService.validate_disposition_quantity(
        production_basis=basis(),
        dispositions=existing,
        disposition_type="WITHDRAWAL",
        quantity_litres=10.0,
    )

    with pytest.raises(ValueError, match="withdrawal litres"):
        MilkReconciliationService.validate_disposition_quantity(
            production_basis=basis(),
            dispositions=existing,
            disposition_type="WITHDRAWAL",
            quantity_litres=11.0,
        )


def test_void_disposition_does_not_consume_available_litres():
    existing = [Disposition(1, 80.0, "SOLD", status="VOID")]
    MilkReconciliationService.validate_disposition_quantity(
        production_basis=basis(),
        dispositions=existing,
        disposition_type="SOLD",
        quantity_litres=80.0,
    )
