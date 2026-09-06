from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from dairyos.finance.opex_attribution import attributed_amount


ROOT = Path(__file__).resolve().parents[1]
COML_API = (ROOT / "src/dairyos/api/coml.py").read_text(encoding="utf-8")
FINANCE_API = (ROOT / "src/dairyos/api/finance_ledger.py").read_text(encoding="utf-8")
FINANCE_UI = (ROOT / "src/DairyOS.Web/src/components/FinanceTab.tsx").read_text(encoding="utf-8")
COP_UI = (ROOT / "src/DairyOS.Web/src/components/COML.tsx").read_text(encoding="utf-8")
PAYROLL_API = (ROOT / "src/dairyos/api/payroll.py").read_text(encoding="utf-8")
TAXONOMY = (ROOT / "src/dairyos/finance/expense_taxonomy.py").read_text(encoding="utf-8")


def row(**kwargs):
    defaults = dict(
        amount=Decimal("300.00"),
        cop_classification="OPEX",
        cop_attribution_method=None,
        cop_service_date=None,
        cop_coverage_start=None,
        cop_coverage_end=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_direct_opex_uses_service_date_not_transaction_date():
    item = row(
        cop_attribution_method="DIRECT",
        cop_service_date=date(2026, 9, 10),
    )
    amount, status = attributed_amount(item, date(2026, 9, 10), date(2026, 9, 10))
    assert status == "ATTRIBUTED"
    assert amount == Decimal("300.00")

    amount, status = attributed_amount(item, date(2026, 9, 9), date(2026, 9, 9))
    assert status == "OUTSIDE_PERIOD"
    assert amount == Decimal("0.00")


def test_periodic_opex_is_prorated_by_overlap_and_counted_once():
    item = row(
        amount=Decimal("3000.00"),
        cop_attribution_method="PERIODIC",
        cop_coverage_start=date(2026, 9, 1),
        cop_coverage_end=date(2026, 9, 30),
    )
    amount, status = attributed_amount(item, date(2026, 9, 15), date(2026, 9, 20))
    assert status == "ATTRIBUTED"
    assert amount == Decimal("600.00")

    full, status = attributed_amount(item, date(2026, 9, 1), date(2026, 9, 30))
    assert status == "ATTRIBUTED"
    assert full == Decimal("3000.00")


def test_non_opex_and_unattributed_opex_never_enter_auto_estimate():
    amount, status = attributed_amount(
        row(cop_classification="NON_OPEX"),
        date(2026, 9, 1),
        date(2026, 9, 30),
    )
    assert status == "NON_OPEX"
    assert amount == Decimal("0.00")

    amount, status = attributed_amount(
        row(cop_attribution_method="ALLOCATED"),
        date(2026, 9, 1),
        date(2026, 9, 30),
    )
    assert status == "UNATTRIBUTED"
    assert amount == Decimal("0.00")


def test_consumption_without_authoritative_usage_link_remains_unattributed():
    amount, status = attributed_amount(
        row(cop_attribution_method="CONSUMPTION"),
        date(2026, 9, 1),
        date(2026, 9, 30),
    )
    assert status == "UNATTRIBUTED"
    assert amount == Decimal("0.00")


def test_integrated_cop_uses_attribution_authority_and_no_transaction_date_hints():
    assert "attributed_amount(" in COML_API
    assert "OPEX_HINTS" not in COML_API
    assert "finance_attributed_opex" in COML_API
    assert "unattributed_opex_count" in COML_API
    assert "non_opex_excluded_total" in COML_API


def test_finance_persists_source_classification_and_attribution_metadata():
    for field in (
        "cop_classification",
        "cop_attribution_method",
        "cop_service_date",
        "cop_coverage_start",
        "cop_coverage_end",
    ):
        assert field in FINANCE_API
    assert "COP classification must be OPEX or NON_OPEX" in FINANCE_API
    assert "Missing attribution dates are allowed to persist" in FINANCE_API


def test_finance_ui_exposes_governed_classification_without_cop_screen_clutter():
    assert "COP Classification & Attribution" in FINANCE_UI
    assert "OPEX — eligible for Estimated COP" in FINANCE_UI
    assert "Non-OPEX — excluded from Estimated COP" in FINANCE_UI
    assert "Estimated OPEX / L" in COP_UI
    assert "Estimated COP / L" in COP_UI
    assert "Operator-Assessed COP" in COP_UI
    assert "Some OPEX is awaiting attribution and is excluded from this estimate." in COP_UI


def test_payroll_uses_authoritative_pay_period_for_opex_attribution():
    assert 'cop_classification="OPEX"' in PAYROLL_API
    assert 'cop_attribution_method="PERIODIC"' in PAYROLL_API
    assert "cop_coverage_start=record.period_start" in PAYROLL_API
    assert "cop_coverage_end=record.period_end" in PAYROLL_API


def test_financing_interest_is_separated_from_bank_service_charges():
    assert '"Loan Interest",' in TAXONOMY
    assert '"Bank Charges",' in TAXONOMY
    assert '"Loan Interest / Bank Charges"' not in TAXONOMY


def test_integrated_cop_resolves_governed_semen_consumption():
    assert "SemenLot" in COML_API
    assert "SemenStockMovement" in COML_API
    assert "purchase_transaction_id == item.id" in COML_API
    assert "SemenStockMovement.signed_quantity < 0" in COML_API
    assert "lot.unit_cost" in COML_API
