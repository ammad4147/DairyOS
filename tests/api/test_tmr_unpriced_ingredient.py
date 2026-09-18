"""An ingredient with no price anywhere must not be costed at zero.

The pricing chain resolves a rate from a Finance FEED purchase, from a
confirmed manual rate, or from the catalogue price. When all three are absent
the older behaviour multiplied the quantity by zero, so the ingredient appeared
free, the ration total looked complete, and cost of production came out lower
than it was with nothing on screen to say why.

The fix is narrow on purpose. The unpriced ingredient is reported as unpriced
and the rest of the ration still costs normally, so one missing price never
withholds the whole figure. That trade is deliberate: a partial cost that says
it is partial is more useful to an operator than no cost at all.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from dairyos.api import tmr as tmr_api


def _ingredient(name: str, *, quantity: float, price: float | None) -> dict:
    return {
        "catalog_name": name,
        "name": name,
        "display_name": name,
        "quantity": quantity,
        "dose_unit": "kg",
        "fallback_price_per_kg": price,
        "price_source": "FINANCE",
    }


@pytest.fixture
def stage(monkeypatch):
    def build(ingredients, price_authority=None):
        monkeypatch.setattr(
            tmr_api, "_stage_ingredients", lambda *a, **k: ingredients
        )
        return tmr_api._priced_stage(
            SimpleNamespace(), "early_milking", price_authority or {}, {}
        )

    return build


def test_an_ingredient_with_no_price_anywhere_is_reported_unpriced(stage):
    result = stage([_ingredient("Mystery Meal", quantity=5.0, price=None)])
    row = result["ingredients"][0]

    assert row["priced"] is False
    assert row["price_source"] == "UNPRICED"
    assert row["cost_per_head_day"] is None, "an unpriced ingredient has no cost"
    assert row["price_per_kg"] is None
    assert result["unpriced_ingredients"] == ["Mystery Meal"]
    assert result["costing_complete"] is False


def test_a_zero_catalogue_price_is_treated_as_no_price(stage):
    """Zero is how an unset catalogue price is stored, not a real free feed."""
    result = stage([_ingredient("Zero Rated", quantity=3.0, price=0.0)])
    assert result["ingredients"][0]["priced"] is False
    assert result["unpriced_ingredients"] == ["Zero Rated"]


def test_one_missing_price_does_not_withhold_the_rest_of_the_ration(stage):
    """The point of the decision: no blockade."""
    result = stage([
        _ingredient("Silage", quantity=20.0, price=25.0),
        _ingredient("Mystery Meal", quantity=5.0, price=None),
    ])

    assert result["cost_per_head_day"] == pytest.approx(500.0), (
        "the priced part of the ration must still produce a cost"
    )
    assert result["ration_kg_per_head_day"] == pytest.approx(25.0), (
        "quantity is known even where price is not"
    )
    assert result["unpriced_ingredients"] == ["Mystery Meal"]
    assert result["costing_complete"] is False


def test_a_fully_priced_ration_reports_itself_complete(stage):
    result = stage([_ingredient("Silage", quantity=20.0, price=25.0)])
    assert result["cost_per_head_day"] == pytest.approx(500.0)
    assert result["unpriced_ingredients"] == []
    assert result["costing_complete"] is True


def test_a_finance_purchase_prices_an_ingredient_with_no_catalogue_price(stage):
    """A missing catalogue price is not missing at all when Finance has one."""
    result = stage(
        [_ingredient("Silage", quantity=20.0, price=None)],
        price_authority={"Silage": {
            "price_per_kg": 25.0, "transaction_id": 1, "purchase_date": "2026-09-01",
        }},
    )
    row = result["ingredients"][0]
    assert row["priced"] is True
    assert row["price_source"] == "FINANCE"
    assert result["costing_complete"] is True
