from pathlib import Path

UI = (
    Path(__file__).resolve().parents[1]
    / "src/DairyOS.Web/src/components/AnimalPassportModal.tsx"
).read_text(encoding="utf-8")


def test_mortality_form_is_mortality_specific():
    assert 'title="Record Mortality"' in UI
    assert 'label="Date of Mortality"' in UI
    assert 'label="Cause of Mortality"' in UI
    assert 'label="Veterinarian / Responsible Person"' in UI
    assert 'label="Notes"' in UI
    assert "disposition:'DECEASED'" in UI
    assert 'buyer_or_counterparty' not in UI
    assert 'exitForm.buyer' not in UI
    assert 'exitForm.amount' not in UI
    assert 'exitForm.reference' not in UI
    assert 'label="Outcome"' not in UI
    assert 'label="Effective Date"' not in UI


def test_mortality_history_is_preserved_and_sale_records_are_not_presented_here():
    assert 'title="Mortality History"' in UI
    assert "item?.disposition||''" in UI
    assert "==='DECEASED'" in UI
    assert "No mortality has been recorded for this animal." in UI
    assert "Animal Passport and all historical records remain preserved." in UI
