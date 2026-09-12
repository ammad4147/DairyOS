from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_finance_ui_exposes_financing_and_animal_purchase_handoff():
    source = (
        ROOT / "src/DairyOS.Web/src/components/FinanceTab.tsx"
    ).read_text(encoding="utf-8")

    for marker in (
        "Owner Investment / Add Money",
        "OWNER_INVESTMENT",
        "Add Money to Finance",
        "Animal Purchase",
        "animal_purchase_categories",
        "onOpenAnimalRegistration",
        "purchaseTransactionId",
        "animal_category",
    ):
        assert marker in source


def test_passport_and_app_complete_the_animal_purchase_link():
    passport = (
        ROOT / "src/DairyOS.Web/src/components/AnimalPassportModal.tsx"
    ).read_text(encoding="utf-8")
    app = (ROOT / "src/DairyOS.Web/src/App.tsx").read_text(
        encoding="utf-8"
    )

    assert "link-animal" in passport
    assert "purchaseCategory" in passport
    assert "categoryLocked" in passport
    assert "purchaseTransactionId={animalRegistrationRequest" in app
