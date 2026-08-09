$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-077 Expense Management Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\commercial\expenses\models",
"dairyos\commercial\expenses\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class FarmExpense:


    expense_id: str

    category: str

    amount: float

    expense_type: str

    status: str

    action: str
'@ | Set-Content `
"dairyos\commercial\expenses\models\farm_expense.py"



@'
from ..models.farm_expense import FarmExpense



class ExpenseManagementService:



    def evaluate(

        self,

        expense_id,

        category,

        amount,

        expense_type

    ):


        if amount > 0:

            status = "ACTIVE"

            action = "Record operating expense"


        else:

            status = "INVALID"

            action = "Review expense entry"



        return FarmExpense(

            expense_id,

            category,

            amount,

            expense_type,

            status,

            action

        )
'@ | Set-Content `
"dairyos\commercial\expenses\services\expense_management_service.py"



@'
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
'@ | Set-Content `
"tests\core\test_expense_management.py"



Write-Host "HERD-077 Expense Management Build Complete"