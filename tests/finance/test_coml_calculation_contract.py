from datetime import date
from decimal import Decimal

from dairyos.api.coml import COMLCalculationRequest, COMLLineItem, calculate_coml


def test_manual_coml_calculation_is_period_and_unit_explicit():
    request = COMLCalculationRequest(
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        milk_produced_liters=Decimal("10000"),
        feed_items=[
            COMLLineItem(item="Silage", quantity=Decimal("5000"), unit="kg", unit_rate=Decimal("20")),
        ],
        operating_items=[
            COMLLineItem(item="Veterinary", quantity=Decimal("4"), unit="visits", unit_rate=Decimal("2500")),
        ],
    )

    result = calculate_coml(request)

    assert result["period_days"] == 31
    assert result["milk_produced_liters"] == "10000"
    assert result["feed_total"] == "100000"
    assert result["operating_total"] == "10000"
    assert Decimal(result["feed_cost_per_liter"]) == Decimal("10")
    assert Decimal(result["opex_cost_per_liter"]) == Decimal("1")
    assert Decimal(result["total_coml_per_liter"]) == Decimal("11")
