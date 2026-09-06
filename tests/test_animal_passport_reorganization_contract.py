from datetime import date
from pathlib import Path
from types import SimpleNamespace

from dairyos.application.animal_passport import LifetimeAnimalPassportService


ROOT = Path(__file__).resolve().parents[1]
PASSPORT_UI = (
    ROOT / "src/DairyOS.Web/src/components/AnimalPassportModal.tsx"
).read_text(encoding="utf-8")


def test_passport_ui_uses_summary_and_history_tables_without_linked_history_tab():
    assert "Linked History" not in PASSPORT_UI
    assert "Lineage & Pedigree" in PASSPORT_UI
    assert "PassportTable" in PASSPORT_UI
    assert 'title="Production Summary"' in PASSPORT_UI
    assert 'title="Lactation History"' in PASSPORT_UI
    assert 'title="Monthly Production"' in PASSPORT_UI
    assert 'title="Clinical History"' in PASSPORT_UI
    assert 'title="Treatment History"' in PASSPORT_UI
    assert 'title="Vaccination History"' in PASSPORT_UI
    assert 'title="Reproductive History"' in PASSPORT_UI
    assert "Detailed daily and milking-session entries remain in the Milk module" in PASSPORT_UI


def test_lineage_is_tabular_and_keeps_passport_navigation_link():
    assert "No lineage or pedigree links recorded." in PASSPORT_UI
    assert "Generation" in PASSPORT_UI
    assert "Relation" in PASSPORT_UI
    assert "Animal ID" in PASSPORT_UI
    assert "lineageLink(row,onOpenPassport)" in PASSPORT_UI


def test_monthly_output_is_governed_from_same_milk_records():
    service = LifetimeAnimalPassportService(repository_factory=None)
    milk = [
        SimpleNamespace(production_date=date(2026, 8, 1), total_yield=20.0),
        SimpleNamespace(production_date=date(2026, 8, 2), total_yield=22.0),
        SimpleNamespace(production_date=date(2026, 9, 1), total_yield=24.0),
    ]

    projection = service._lactation_projection(
        milk=milk,
        breeding=[],
        as_of_date=date(2026, 9, 6),
    )

    assert projection["lifetime"]["lifetime_milk_liters"] == 66.0
    assert projection["monthly_output"] == [
        {
            "month": "2026-09",
            "milk_liters": 24.0,
            "recorded_days": 1,
            "average_liters_per_recorded_day": 24.0,
            "peak_daily_yield_liters": 24.0,
            "peak_daily_yield_date": "2026-09-01",
        },
        {
            "month": "2026-08",
            "milk_liters": 42.0,
            "recorded_days": 2,
            "average_liters_per_recorded_day": 21.0,
            "peak_daily_yield_liters": 22.0,
            "peak_daily_yield_date": "2026-08-02",
        },
    ]
