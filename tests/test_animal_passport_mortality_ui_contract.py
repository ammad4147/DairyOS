from pathlib import Path

UI = (
    Path(__file__).resolve().parents[1]
    / "src/DairyOS.Web/src/components/AnimalPassportModal.tsx"
).read_text(encoding="utf-8")


def test_mortality_form_is_mortality_specific():
    assert "['exit','Mortality']" in UI
    assert 'title={mortalityRecorded?"Mortality Record":"Record Mortality"}' in UI
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


def test_mortality_record_freezes_after_registration_without_history_table():
    assert "mortalityRecorded?" in UI
    assert "<FrozenField" in UI
    assert "Mortality History" not in UI
    assert "No mortality has been recorded for this animal." not in UI
    assert "This final lifecycle record is frozen in the Animal Passport" in UI
    assert "if(isNew||mortalityRecorded)return" in UI
    assert "all existing DairyOS linkages and historical records remain available" in UI


def test_mortality_submission_keeps_existing_disposition_linkage():
    assert "/disposition" in UI
    assert "setAnimal(result.animal)" in UI
    assert "onSave?.(toUi(result.animal))" in UI
    assert "await load()" in UI
