$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-087 Financial Forecast Engine Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\intelligence\finance\models",
"dairyos\intelligence\finance\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class FinancialForecast:


    period: str

    milk_output: float

    milk_price: float

    revenue: float

    expenses: float

    profit: float

    status: str
'@ | Set-Content `
"dairyos\intelligence\finance\models\financial_forecast.py"



@'
from ..models.financial_forecast import FinancialForecast



class FinancialForecastService:



    def forecast(

        self,

        period,

        milk_output,

        milk_price,

        expenses

    ):


        revenue = milk_output * milk_price


        profit = revenue - expenses



        if profit > 0:

            status = "POSITIVE"



        elif profit == 0:

            status = "BREAK_EVEN"



        else:

            status = "NEGATIVE"



        return FinancialForecast(

            period,

            milk_output,

            milk_price,

            revenue,

            expenses,

            profit,

            status

        )
'@ | Set-Content `
"dairyos\intelligence\finance\services\financial_forecast_service.py"



@'
from dairyos.intelligence.finance.services.financial_forecast_service import FinancialForecastService



def test_period():

    result = FinancialForecastService().forecast(

        "MONTHLY",

        18750,

        225,

        3000000

    )

    assert result.period == "MONTHLY"



def test_milk_output():

    result = FinancialForecastService().forecast(

        "MONTHLY",

        18750,

        225,

        3000000

    )

    assert result.milk_output == 18750



def test_price():

    result = FinancialForecastService().forecast(

        "MONTHLY",

        18750,

        225,

        3000000

    )

    assert result.milk_price == 225



def test_revenue():

    result = FinancialForecastService().forecast(

        "MONTHLY",

        18750,

        225,

        3000000

    )

    assert result.revenue == 4218750



def test_expenses():

    result = FinancialForecastService().forecast(

        "MONTHLY",

        18750,

        225,

        3000000

    )

    assert result.expenses == 3000000



def test_profit():

    result = FinancialForecastService().forecast(

        "MONTHLY",

        18750,

        225,

        3000000

    )

    assert result.profit == 1218750



def test_positive_status():

    result = FinancialForecastService().forecast(

        "MONTHLY",

        18750,

        225,

        3000000

    )

    assert result.status == "POSITIVE"



def test_break_even():

    result = FinancialForecastService().forecast(

        "MONTHLY",

        1000,

        100,

        100000

    )

    assert result.status == "BREAK_EVEN"



def test_negative():

    result = FinancialForecastService().forecast(

        "MONTHLY",

        1000,

        100,

        200000

    )

    assert result.status == "NEGATIVE"



def test_service_exists():

    assert FinancialForecastService is not None
'@ | Set-Content `
"tests\core\test_financial_forecasting.py"



Write-Host "HERD-087 Financial Forecast Engine Build Complete"