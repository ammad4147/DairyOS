from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FINANCE = (ROOT / "src/DairyOS.Web/src/components/FinanceTab.tsx").read_text(encoding="utf-8")
BREEDING = (ROOT / "src/DairyOS.Web/src/components/BreedingTab.tsx").read_text(encoding="utf-8")


def test_finance_has_special_semen_purchase_details():
    assert "Semen Purchase Details" in FINANCE
    assert "Sire / Bull Code" in FINANCE
    assert "Batch / Lot Number" in FINANCE
    assert "Storage Tank / Location" in FINANCE
    assert "semen_batch_number: isSemenPurchase ? semenBatch : null" in FINANCE


def test_breeding_ai_selects_available_purchased_semen_only():
    assert "/farm/breeding/semen-stock" in BREEDING
    assert "Available Purchased Semen" in BREEDING
    assert "No purchased semen stock is available" in BREEDING
    assert "semen_lot_id" in BREEDING
    assert "Semen Lot / Batch Performance" in BREEDING
    assert "Semen Supplier Performance" in BREEDING
