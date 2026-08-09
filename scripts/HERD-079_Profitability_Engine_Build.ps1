$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-079 Profitability Engine Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\finance\profitability\models",
"dairyos\finance\profitability\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class ProfitabilitySummary:


    revenue: float

    expenses: float

    operating_profit: float

    profit_margin: float

    status: str

    action: str
'@ | Set-Content `
"dairyos\finance\profitability\models\profitability_summary.py"



@'
from ..models.profitability_summary import ProfitabilitySummary



class ProfitabilityService:



    def evaluate(

        self,

        revenue,

        expenses

    ):


        operating_profit = revenue - expenses



        if revenue > 0:

            profit_margin = (

                operating_profit /

                revenue

            ) * 100

        else:

            profit_margin = 0



        if operating_profit > 0:

            status = "PROFITABLE"

            action = "Continue current strategy"



        elif operating_profit == 0:

            status = "BREAK EVEN"

            action = "Monitor performance"



        else:

            status = "LOSS"

            action = "Immediate corrective action required"



        return ProfitabilitySummary(

            revenue,

            expenses,

            operating_profit,

            profit_margin,

            status,

            action

        )
'@ | Set-Content `
"dairyos\finance\profitability\services\profitability_service.py"



@'
from dairyos.finance.profitability.services.profitability_service import ProfitabilityService



def test_revenue():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.revenue == 4200000



def test_expenses():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.expenses == 3500000



def test_operating_profit():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.operating_profit == 700000



def test_profit_margin():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert round(result.profit_margin, 2) == 16.67



def test_profitable_status():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.status == "PROFITABLE"



def test_profitable_action():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.action == "Continue current strategy"



def test_break_even():

    result = ProfitabilityService().evaluate(

        1000000,

        1000000

    )

    assert result.status == "BREAK EVEN"



def test_loss():

    result = ProfitabilityService().evaluate(

        100000,

        200000

    )

    assert result.status == "LOSS"



def test_loss_action():

    result = ProfitabilityService().evaluate(

        100000,

        200000

    )

    assert result.action == "Immediate corrective action required"



def test_profitability_command():

    result = ProfitabilityService().evaluate(

        4200000,

        3500000

    )

    assert result.operating_profit == 700000
'@ | Set-Content `
"tests\core\test_profitability.py"



Write-Host "HERD-079 Profitability Engine Build Complete"