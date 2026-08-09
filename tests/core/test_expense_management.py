from dairyos.commercial.expenses.services.expense_management_service import ExpenseManagementService



def test_expense_id():

    result = ExpenseManagementService().evaluate(

        "EXP-001",

        "Feed Cost",

        1875000,

        "Operating Expense"

    )

    assert result.expense_id == "EXP-001"



def test_category():

    result = ExpenseManagementService().evaluate(

        "EXP-001",

        "Feed Cost",

        1875000,

        "Operating Expense"

    )

    assert result.category == "Feed Cost"



def test_amount():

    result = ExpenseManagementService().evaluate(

        "EXP-001",

        "Feed Cost",

        1875000,

        "Operating Expense"

    )

    assert result.amount == 1875000



def test_expense_type():

    result = ExpenseManagementService().evaluate(

        "EXP-001",

        "Feed Cost",

        1875000,

        "Operating Expense"

    )

    assert result.expense_type == "Operating Expense"



def test_active_status():

    result = ExpenseManagementService().evaluate(

        "EXP-001",

        "Feed Cost",

        1875000,

        "Operating Expense"

    )

    assert result.status == "ACTIVE"



def test_active_action():

    result = ExpenseManagementService().evaluate(

        "EXP-001",

        "Feed Cost",

        1875000,

        "Operating Expense"

    )

    assert result.action == "Record operating expense"



def test_zero_expense():

    result = ExpenseManagementService().evaluate(

        "EXP-002",

        "Other",

        0,

        "Operating Expense"

    )

    assert result.status == "INVALID"



def test_zero_action():

    result = ExpenseManagementService().evaluate(

        "EXP-002",

        "Other",

        0,

        "Operating Expense"

    )

    assert result.action == "Review expense entry"



def test_expense_flow():

    result = ExpenseManagementService().evaluate(

        "EXP-003",

        "Labour",

        500000,

        "Operating Expense"

    )

    assert result.status == "ACTIVE"



def test_command_status():

    result = ExpenseManagementService().evaluate(

        "EXP-004",

        "Utilities",

        100000,

        "Operating Expense"

    )

    assert result.action == "Record operating expense"
