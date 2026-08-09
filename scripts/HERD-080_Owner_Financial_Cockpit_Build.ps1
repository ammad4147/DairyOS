$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-080 Owner Financial Cockpit Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\finance\cockpit\models",
"dairyos\finance\cockpit\services",
"tests\core",
"scripts" | Out-Null


@'
from dataclasses import dataclass



@dataclass
class OwnerFinancialCockpit:


    revenue: float

    expenses: float

    profit: float

    cash_position: float

    financial_status: str

    owner_action: str
'@ | Set-Content `
"dairyos\finance\cockpit\models\owner_financial_cockpit.py"



@'
from ..models.owner_financial_cockpit import OwnerFinancialCockpit



class OwnerFinancialCockpitService:



    def evaluate(

        self,

        revenue,

        expenses,

        cash_position

    ):


        profit = revenue - expenses



        if profit > 0 and cash_position >= 0:

            financial_status = "HEALTHY"

            owner_action = "Continue operations"



        elif cash_position < 0:

            financial_status = "CASH RISK"

            owner_action = "Immediate intervention required"



        else:

            financial_status = "ATTENTION"

            owner_action = "Review business performance"



        return OwnerFinancialCockpit(

            revenue,

            expenses,

            profit,

            cash_position,

            financial_status,

            owner_action

        )
'@ | Set-Content `
"dairyos\finance\cockpit\services\owner_financial_cockpit_service.py"



@'
from dairyos.finance.cockpit.services.owner_financial_cockpit_service import OwnerFinancialCockpitService



def test_profit():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.profit == 700000



def test_cash():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.cash_position == 5700000



def test_status():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.financial_status == "HEALTHY"



def test_action():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.owner_action == "Continue operations"



def test_revenue():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.revenue == 4200000



def test_expenses():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.expenses == 3500000



def test_cash_risk():

    result = OwnerFinancialCockpitService().evaluate(

        100000,

        200000,

        -50000

    )

    assert result.financial_status == "CASH RISK"



def test_cash_action():

    result = OwnerFinancialCockpitService().evaluate(

        100000,

        200000,

        -50000

    )

    assert result.owner_action == "Immediate intervention required"



def test_attention():

    result = OwnerFinancialCockpitService().evaluate(

        100000,

        100000,

        50000

    )

    assert result.financial_status == "ATTENTION"



def test_command():

    result = OwnerFinancialCockpitService().evaluate(

        4200000,

        3500000,

        5700000

    )

    assert result.profit == 700000
'@ | Set-Content `
"tests\core\test_owner_financial_cockpit.py"


Write-Host "HERD-080 Owner Financial Cockpit Build Complete"