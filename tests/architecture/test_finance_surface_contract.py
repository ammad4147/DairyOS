from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FINANCE_TAB = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "FinanceTab.tsx"


def test_finance_surface_keeps_one_payables_summary_without_duplicate_panel():
    text = FINANCE_TAB.read_text(encoding="utf-8-sig")

    assert "['Payables',payableTotal" in text
    assert "/farm/finance-ledger/payables" not in text
    assert "type Payables=" not in text
    assert ">Payables</div>" not in text


def test_finance_ledgers_retain_visible_void_audit_trail():
    text = FINANCE_TAB.read_text(encoding="utf-8-sig")

    assert "Revenue Ledger" in text
    assert "Accounting Expense Ledger" in text
    assert "textDecoration:isVoid?'line-through':'none'" in text
    assert "VOID: {reason||'See audit trail'}" in text
