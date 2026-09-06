from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "FinanceTab.tsx"
)


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8-sig")


def test_animal_sale_dropdown_uses_exact_canonical_category_match():
    source = _source()

    assert "'Male Calf Sale': 'MALE_CALF'" in source
    assert "'Female Calf Sale': 'FEMALE_CALF'" in source
    assert "normalizeCategory(animal.category) === expectedCategory" in source
    assert "tokens.every(token => hay.includes(token))" not in source


def test_specific_animal_sale_persists_one_head_and_quantity_is_not_editable():
    source = _source()

    assert "quantity: isAnimalSale ? 1" in source
    assert "unit: isAnimalSale ? 'head'" in source
    assert 'aria-label="Animal sale quantity"' in source
    assert 'value="1" readOnly disabled' in source
