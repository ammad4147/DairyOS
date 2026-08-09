$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-078 Cash Flow Engine Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\finance\cashflow\models",
"dairyos\finance\cashflow\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class CashFlowSummary:


    opening_cash: float

    income: float

    expenses: float

    net_cash_movement: float

    closing_cash: float

    status: str

    action: str
'@ | Set-Content `
"dairyos\finance\cashflow\models\cash_flow_summary.py"



@'
from ..models.cash_flow_summary import CashFlowSummary



class CashFlowService:



    def evaluate(

        self,

        opening_cash,

        income,

        expenses

    ):


        net_cash_movement = income - expenses

        closing_cash = opening_cash + net_cash_movement



        if closing_cash >= 0:

            status = "POSITIVE"

            action = "Maintain current operations"



        else:

            status = "NEGATIVE"

            action = "Immediate cash recovery required"



        return CashFlowSummary(

            opening_cash,

            income,

            expenses,

            net_cash_movement,

            closing_cash,

            status,

            action

        )
'@ | Set-Content `
"dairyos\finance\cashflow\services\cash_flow_service.py"



@'
from dairyos.finance.cashflow.services.cash_flow_service import CashFlowService



def test_opening_cash():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.opening_cash == 5000000



def test_income():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.income == 4200000



def test_expenses():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.expenses == 3500000



def test_net_cash():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.net_cash_movement == 700000



def test_closing_cash():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.closing_cash == 5700000



def test_positive_status():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.status == "POSITIVE"



def test_positive_action():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.action == "Maintain current operations"



def test_negative_cash():

    result = CashFlowService().evaluate(

        100000,

        50000,

        200000

    )

    assert result.status == "NEGATIVE"



def test_negative_action():

    result = CashFlowService().evaluate(

        100000,

        50000,

        200000

    )

    assert result.action == "Immediate cash recovery required"



def test_cashflow_command():

    result = CashFlowService().evaluate(

        5000000,

        4200000,

        3500000

    )

    assert result.closing_cash == 5700000
'@ | Set-Content `
"tests\core\test_cash_flow.py"



Write-Host "HERD-078 Cash Flow Engine Build Complete"