from __future__ import annotations

from types import SimpleNamespace

import pytest

from dairyos.api.feed_inventory import _tmr_ingredient_requirement
from dairyos.api.tmr import _category_costs
from dairyos.core.tmr_stage_authority import (
    allowed_stages_for_category,
    normalize_stage,
    validate_stage_for_category,
)


def test_governed_stage_aliases_normalize_to_canonical_values():
    assert normalize_stage("Early Lactation") == "early_milking"
    assert normalize_stage("close-up dry") == "close_up"
    assert normalize_stage("bull") == "bull"


def test_invalid_or_cross_category_stage_is_rejected():
    with pytest.raises(ValueError, match="not valid for Milking"):
        validate_stage_for_category("Milking", "close_up")

    with pytest.raises(ValueError, match="Unknown TMR production group"):
        validate_stage_for_category("Dry", "free text stage")


def test_single_stage_categories_have_one_unambiguous_authority():
    assert allowed_stages_for_category("Heifer") == ("heifer_growth",)
    assert allowed_stages_for_category("Female Calf") == ("calf_starter",)
    assert allowed_stages_for_category("Male Calf") == ("calf_starter",)
    assert allowed_stages_for_category("Bull") == ("bull",)


def test_category_cost_uses_exact_stage_population_not_equal_stage_average():
    stages = {
        "early_milking": {"cost_per_head_day": 10.0},
        "mid_milking": {"cost_per_head_day": 20.0},
        "late_milking": {"cost_per_head_day": 30.0},
        "far_off": {"cost_per_head_day": 0.0},
        "close_up": {"cost_per_head_day": 0.0},
        "heifer_growth": {"cost_per_head_day": 0.0},
        "calf_starter": {"cost_per_head_day": 0.0},
        "bull": {"cost_per_head_day": 0.0},
    }
    counts = {"Milking": 3}
    rows = _category_costs(
        stages,
        counts,
        stage_counts={
            "early_milking": 2,
            "mid_milking": 0,
            "late_milking": 1,
        },
        unallocated={"Milking": 0},
    )
    milking = next(row for row in rows if row["category"] == "Milking")

    # Management estimate remains the simple average: 20/head * 3 = 60.
    assert milking["category_cost_per_day"] == 60.0

    # Authority is actual population weighting: 2*10 + 0*20 + 1*30 = 50.
    assert milking["authoritative_category_cost_per_day"] == 50.0
    assert milking["allocation_complete"] is True


def test_feed_storage_requirement_uses_exact_stage_population():
    summary = {
        "stage_allocation_complete": True,
        "price_authority_complete": True,
        "stages": {
            "early_milking": {
                "ingredients": [
                    {
                        "catalog_name": "Silage",
                        "quantity": 10,
                        "dose_unit": "kg",
                    }
                ]
            },
            "late_milking": {
                "ingredients": [
                    {
                        "catalog_name": "Silage",
                        "quantity": 2,
                        "dose_unit": "kg",
                    }
                ]
            },
        },
        "categories": [
            {
                "category": "Milking",
                "stage_keys": ["early_milking", "late_milking"],
                "stage_counts": {"early_milking": 2, "late_milking": 1},
                "allocation_complete": True,
            }
        ],
    }

    # 2 early cows * 10 kg + 1 late cow * 2 kg = 22 kg/day.
    assert _tmr_ingredient_requirement(summary) == {"Silage": 22.0}


def test_feed_storage_fails_closed_only_when_stage_quantity_authority_is_incomplete():
    base = {
        "stage_allocation_complete": False,
        "price_authority_complete": True,
        "stages": {},
        "categories": [],
    }
    with pytest.raises(ValueError, match="stage allocation is incomplete"):
        _tmr_ingredient_requirement(base)


def test_feed_storage_quantity_does_not_depend_on_price_authority():
    summary = {
        "stage_allocation_complete": True,
        "price_authority_complete": False,
        "stages": {
            "heifer_growth": {
                "ingredients": [
                    {
                        "catalog_name": "Silage",
                        "quantity": 5,
                        "dose_unit": "kg",
                    }
                ]
            }
        },
        "categories": [
            {
                "category": "Heifer",
                "stage_keys": ["heifer_growth"],
                "stage_counts": {"heifer_growth": 2},
                "allocation_complete": True,
            }
        ],
    }
    assert _tmr_ingredient_requirement(summary) == {"Silage": 10.0}


def test_passport_uses_governed_stage_selector_not_free_text():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    source = (
        root
        / "src"
        / "DairyOS.Web"
        / "src"
        / "components"
        / "AnimalPassportModal.tsx"
    ).read_text(encoding="utf-8")

    assert 'label="Production Group / TMR Stage"' in source
    assert "Select governed TMR stage" in source
    assert "early_milking" in source
    assert "close_up" in source
    assert '<input value={form.productionGroup}' not in source


def test_registration_rejects_cross_category_tmr_stage(client):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "animal_category": "Milking",
            "milking_frequency": "THRICE_DAILY",
            "production_group": "close_up",
        },
    )
    assert response.status_code == 422
    assert "not valid for Milking" in response.json()["detail"]




def test_single_stage_registration_rejects_explicit_wrong_stage(client):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "animal_category": "Heifer",
            "production_group": "bull",
        },
    )
    assert response.status_code == 422
    assert "not valid for Heifer" in response.json()["detail"]

def test_single_stage_registration_is_auto_governed(client):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "animal_category": "Heifer",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["production_group"] == "heifer_growth"


def test_multistage_registration_persists_explicit_governed_stage(client):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "animal_category": "Milking",
            "milking_frequency": "THRICE_DAILY",
            "production_group": "early_milking",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["production_group"] == "early_milking"
