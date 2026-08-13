"""The herd average must not be diluted by sessions nobody entered (G1.6)."""

from dairyos.api.dairy_kpi import _has_entered_yield
from dairyos.data.models.milk_production import MilkProduction


def test_a_record_with_no_entered_yield_is_not_an_observation():
    record = MilkProduction(animal_id="AN-1")

    assert record.morning_yield is None
    assert _has_entered_yield(record) is False


def test_an_entered_zero_is_an_observation():
    record = MilkProduction(animal_id="AN-1", morning_yield=0.0)

    assert _has_entered_yield(record) is True


def test_a_partial_entry_is_an_observation():
    record = MilkProduction(animal_id="AN-1", evening_yield=6.0)

    assert _has_entered_yield(record) is True


def test_calculate_total_preserves_null_when_nothing_was_entered():
    record = MilkProduction(animal_id="AN-1")

    assert record.calculate_total() is None


def test_calculate_total_sums_only_entered_sessions():
    record = MilkProduction(
        animal_id="AN-1",
        morning_yield=9.0,
        evening_yield=7.0,
    )

    assert record.calculate_total() == 16.0


def test_an_entered_zero_totals_to_zero_not_null():
    record = MilkProduction(animal_id="AN-1", morning_yield=0.0)

    assert record.calculate_total() == 0.0
