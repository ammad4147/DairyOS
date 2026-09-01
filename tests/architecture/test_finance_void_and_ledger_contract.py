from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "src" / "dairyos" / "api" / "finance_ledger.py"
UI = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "FinanceTab.tsx"


def test_duplicate_payables_endpoint_is_retired():
    api = API.read_text(encoding="utf-8-sig")
    assert '@router.get("/payables")' not in api
    assert '@router.get("/ageing")' in api


def test_received_revenue_is_governedly_voidable():
    api = API.read_text(encoding="utf-8-sig")
    assert '"RECEIVED": frozenset({"RECEIVED", "VOID"})' in api


def test_linked_milk_sale_void_preserves_original_business_facts():
    api = API.read_text(encoding="utf-8-sig")
    preserved = 'elif status == "VOID":\n        disposition.status = "VOID"\n        disposition.notes = transaction.notes'
    destructive = 'elif status == "VOID":\n        disposition.status = "VOID"\n        disposition.quantity_litres = 0.0\n        disposition.amount_due = 0.0\n        disposition.amount_received = 0.0'
    assert preserved in api
    assert destructive not in api


def test_finance_ledgers_share_clean_accounting_columns_and_revenue_void_action():
    ui = UI.read_text(encoding="utf-8-sig")
    for label in ("Date", "Particulars", "Counterparty", "Reference", "Status", "Amount"):
        assert label in ui
    assert "Customer / Buyer" in ui
    assert "buyer_or_counterparty:revCounterparty||null" in ui
    assert ">Received</button>" in ui
    assert "setVoidTarget(r)" in ui
    assert "['Payables',payableTotal" in ui
    assert "/farm/finance-ledger/payables" not in ui
