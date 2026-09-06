from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_finance_record_expense_uses_two_part_category_selector():
    source = text("src/DairyOS.Web/src/components/FinanceTab.tsx")

    assert "Record Expense" in source
    assert "aria-label=\"Expense category group\"" in source
    assert "aria-label=\"Expense list item\"" in source
    assert "selectExpenseGroup" in source
    assert "expenseItems.map(item" in source
    assert "gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)'" in source
    assert "<optgroup" not in source


def test_opex_taxonomy_is_refined_for_dairy_operating_expenses():
    source = text("src/dairyos/finance/expense_taxonomy.py")

    for group in (
        "VETERINARY_HERD_HEALTH",
        "BREEDING_REPRODUCTION",
        "LABOR_SALARIES",
        "UTILITIES_ENERGY",
        "MACHINERY_INFRASTRUCTURE",
        "DAIRY_CHEMICALS_HYGIENE",
        "BEDDING_HOUSING_WASTE",
        "LOGISTICS_ADMIN_FINANCE",
        "LAND_RENT_CUSTOM_SERVICES",
        "CUSTOM",
    ):
        assert f'"{group}": [' in source

    for item in (
        "Lab Testing & Diagnostics",
        "Hoof Trimming & Lameness Treatment",
        "Pregnancy Diagnosis / Ultrasound",
        "Overtime / Bonus Payments",
        "Farm Vehicle Fuel & Maintenance",
        "Milk Filters / Strainers",
        "Manure Handling / Removal",
        "Insurance Premiums",
        "Loan Interest",
        "Bank Charges",
        "Custom Hire / Contract Services",
    ):
        assert f'"{item}"' in source


def test_equipment_purchase_remains_available_for_named_assets():
    taxonomy_source = text("src/dairyos/finance/expense_taxonomy.py")
    api_source = text("src/dairyos/api/finance_ledger.py")

    assert '"Equipment Purchase"' in taxonomy_source
    assert 'EQUIPMENT_PURCHASE_ITEM = "Equipment Purchase"' in api_source
    assert "custom_specification is required" in api_source
    policy_source = text("src/dairyos/finance/opex_attribution.py")
    assert '"Equipment Purchase"' in policy_source
    assert '"NON_OPEX"' in policy_source
