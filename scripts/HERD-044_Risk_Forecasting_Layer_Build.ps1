$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-044 Risk Forecasting Layer Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class RiskForecast:


    category: str

    forecast: str

    probability: int

    risk_level: str

    recommended_action: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\risk_forecast.py"



@'
from ..models.risk_forecast import RiskForecast



class RiskForecastService:



    def generate(

        self,

        category,

        signal_confidence,

        trend_strength

    ):


        probability = min(

            signal_confidence + trend_strength,

            95

        )


        if probability >= 75:

            risk_level = "HIGH"

        elif probability >= 50:

            risk_level = "MEDIUM"

        else:

            risk_level = "LOW"



        return RiskForecast(

            category,

            f"{category} future risk forecast",

            probability,

            risk_level,

            self._action(category)

        )



    def _action(

        self,

        category

    ):


        actions = {

            "PRODUCTION":

                "Review feed and production factors",

            "HEALTH":

                "Review animal health prevention",

            "REPRODUCTION":

                "Review breeding strategy",

            "FINANCE":

                "Review financial planning"

        }


        return actions.get(

            category,

            "Review farm indicators"

        )



    def requires_action(

        self,

        forecast

    ):


        return forecast.risk_level in (

            "HIGH",

            "MEDIUM"

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\risk_forecast_service.py"



@'
from dairyos.herd.dashboard.services.risk_forecast_service import RiskForecastService



def test_forecast_creation():

    forecast = RiskForecastService().generate(

        "PRODUCTION",

        80,

        0

    )

    assert forecast.category == "PRODUCTION"



def test_high_risk():

    forecast = RiskForecastService().generate(

        "PRODUCTION",

        80,

        0

    )

    assert forecast.risk_level == "HIGH"



def test_medium_risk():

    forecast = RiskForecastService().generate(

        "HEALTH",

        40,

        15

    )

    assert forecast.risk_level == "MEDIUM"



def test_low_risk():

    forecast = RiskForecastService().generate(

        "FINANCE",

        20,

        5

    )

    assert forecast.risk_level == "LOW"



def test_probability_limit():

    forecast = RiskForecastService().generate(

        "HEALTH",

        90,

        20

    )

    assert forecast.probability == 95



def test_production_action():

    forecast = RiskForecastService().generate(

        "PRODUCTION",

        80,

        0

    )

    assert forecast.recommended_action == "Review feed and production factors"



def test_health_action():

    forecast = RiskForecastService().generate(

        "HEALTH",

        80,

        0

    )

    assert forecast.recommended_action == "Review animal health prevention"



def test_reproduction_action():

    forecast = RiskForecastService().generate(

        "REPRODUCTION",

        80,

        0

    )

    assert forecast.recommended_action == "Review breeding strategy"



def test_requires_action():

    service = RiskForecastService()

    forecast = service.generate(

        "PRODUCTION",

        80,

        0

    )

    assert service.requires_action(forecast)



def test_model():

    forecast = RiskForecastService().generate(

        "FINANCE",

        20,

        5

    )

    assert forecast.forecast == "FINANCE future risk forecast"
'@ | Set-Content `
"tests\core\test_risk_forecast.py"



Write-Host "HERD-044 Risk Forecasting Layer Build Complete"