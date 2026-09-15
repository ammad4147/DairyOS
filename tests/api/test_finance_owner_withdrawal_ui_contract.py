from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FINANCE = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "FinanceTab.tsx"
).read_text(encoding="utf-8")


def test_owner_withdrawal_is_exposed_as_financing_cash_outflow():
    assert "Owner Draw / Withdraw Money" in FINANCE
    assert "'OWNER_WITHDRAWAL'" in FINANCE
    assert "const isOwnerWithdrawal" in FINANCE
    assert "const isOwnerWithdrawalEntry" in FINANCE
    assert "const isOwnerFinancing" in FINANCE
    assert "Owner Draw / Withdrawal" in FINANCE
    assert "'Owner Draw'" in FINANCE
    assert "const ledgerType = (t: Transaction) =>" in FINANCE


def test_owner_withdrawal_reduces_cash_without_becoming_expense():
    assert (
        "const netCash = cashRevenue + capitalAdded - totalExpenses - "
        "ownerWithdrawals;"
    ) in FINANCE
    assert "periodOwnerWithdrawals" in FINANCE
    assert "statusOwnerWithdrawals" in FINANCE
    assert "periodOperatingNet = periodRevenue - periodExpenses" in FINANCE

    assert (
        "const isExpense = (t: Transaction) =>\n"
        "  t.transaction_type === 'EXPENSE' || "
        "t.transaction_type === 'PAYMENT';"
    ) in FINANCE


def test_owner_withdrawal_submission_is_immediate_financing_movement():
    assert (
        "isOwnerWithdrawalEntry\n"
        "              ? 'OWNER_WITHDRAWAL'"
    ) in FINANCE
    assert (
        "payment_method: isOwnerFinancing || revStatus === 'RECEIVED' "
        "? 'CASH' : 'CREDIT'"
    ) in FINANCE
    assert "status: isOwnerFinancing ? 'RECEIVED' : revStatus" in FINANCE
    assert (
        "due_date: isOwnerFinancing || revStatus !== 'RECEIVABLE' "
        "? null : revDueDate"
    ) in FINANCE
    assert "!isOwnerFinancing && revStatus === 'RECEIVABLE'" in FINANCE


def test_owner_withdrawal_operator_notice_preserves_accounting_semantics():
    assert "Owner Draw / Withdrawal is a financing cash outflow." in FINANCE
    assert "It reduces cash position but is excluded from revenue" in FINANCE
    assert "farm expense, OPEX, CAPEX and Estimated COP." in FINANCE


def test_owner_withdrawal_has_operator_specific_controls():
    assert (
        "value={isOwnerInvestment ? 'Cash contribution' : "
        "'Owner withdrawal'}"
    ) in FINANCE
    assert "Cash Withdrawn" in FINANCE
    assert "Owner / Recipient (optional)" in FINANCE
    assert "Record Owner Draw" in FINANCE


def test_void_owner_withdrawal_is_zero_cash_movement():
    assert (
        "String(t.status || '').toUpperCase() === 'VOID' ? 0 "
        ": Number(t.amount || 0)"
    ) in FINANCE
    assert (
        "exploredRows.filter(isOwnerWithdrawal)"
        ".reduce((sum, t) => sum + activeAmount(t), 0)"
    ) in FINANCE


def test_owner_withdrawal_is_not_mislabelled_as_expense_in_explorer():
    assert (
        "const ledgerType = (t: Transaction) => isCapitalInflow(t)"
    ) in FINANCE
    assert "isOwnerWithdrawal(t)" in FINANCE
    assert "{ledgerType(r)}</span>" in FINANCE
    assert "'Owner Draw': periodOwnerWithdrawals" in FINANCE
    assert "'Operating Net': periodOperatingNet" in FINANCE
    assert "'Cash Movement': periodNet" in FINANCE


def test_owner_withdrawal_form_boolean_does_not_shadow_transaction_predicate():
    assert "const isOwnerWithdrawal = (t: Transaction) =>" in FINANCE
    assert (
        "const isOwnerWithdrawalEntry = "
        "revCategory === 'Owner Draw / Withdraw Money';"
    ) in FINANCE
    assert "const isOwnerWithdrawal = revCategory" not in FINANCE
    assert ".filter(isOwnerWithdrawal)" in FINANCE
    assert "isOwnerWithdrawal(t)" in FINANCE
    assert "ledgerType(r)" in FINANCE
