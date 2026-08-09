$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-028 Farm Command Center Recommendation Engine Build"

New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null


@'
from dataclasses import dataclass


@dataclass
class Recommendation:

    category: str

    issue: str

    recommendation: str

    priority: str

    timeframe: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\recommendation.py"



@'
from ..models.recommendation import Recommendation


class RecommendationService:


    def generate(

        self,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False,

        financial_status="POSITIVE",

        production_status="STABLE"

    ):


        recommendations = []



        if replacement_shortage:

            recommendations.append(

                Recommendation(

                    "HERD STRATEGY",

                    "Replacement pipeline shortage",

                    "Secure replacement animals to protect future production",

                    "HIGH",

                    "30 days"

                )

            )



        if health_alerts > 0:

            recommendations.append(

                Recommendation(

                    "ANIMAL HEALTH",

                    "Health alerts detected",

                    "Review animal health cases and treatment plans",

                    "HIGH",

                    "7 days"

                )

            )



        if open_cows > 3:

            recommendations.append(

                Recommendation(

                    "REPRODUCTION",

                    "High open cow count",

                    "Review breeding performance",

                    "MEDIUM",

                    "14 days"

                )

            )



        if financial_status != "POSITIVE":

            recommendations.append(

                Recommendation(

                    "FINANCE",

                    "Financial pressure detected",

                    "Review cost controls and cash position",

                    "MEDIUM",

                    "14 days"

                )

            )



        if production_status != "STABLE":

            recommendations.append(

                Recommendation(

                    "PRODUCTION",

                    "Production performance issue",

                    "Investigate milk production performance",

                    "MEDIUM",

                    "7 days"

                )

            )



        return recommendations
'@ | Set-Content `
"dairyos\herd\dashboard\services\recommendation_service.py"



@'
from dairyos.herd.dashboard.services.recommendation_service import RecommendationService



def test_recommendation_creation():

    result = RecommendationService().generate(

        replacement_shortage=True

    )

    assert len(result) == 1



def test_replacement_recommendation():

    result = RecommendationService().generate(

        replacement_shortage=True

    )

    assert result[0].category == "HERD STRATEGY"



def test_replacement_priority():

    result = RecommendationService().generate(

        replacement_shortage=True

    )

    assert result[0].priority == "HIGH"



def test_health_recommendation():

    result = RecommendationService().generate(

        health_alerts=2

    )

    assert result[0].category == "ANIMAL HEALTH"



def test_reproduction_recommendation():

    result = RecommendationService().generate(

        open_cows=5

    )

    assert result[0].category == "REPRODUCTION"



def test_finance_recommendation():

    result = RecommendationService().generate(

        financial_status="WARNING"

    )

    assert result[0].category == "FINANCE"



def test_production_recommendation():

    result = RecommendationService().generate(

        production_status="LOW"

    )

    assert result[0].category == "PRODUCTION"



def test_multiple_recommendations():

    result = RecommendationService().generate(

        health_alerts=1,

        replacement_shortage=True

    )

    assert len(result) == 2



def test_timeframe_exists():

    result = RecommendationService().generate(

        replacement_shortage=True

    )

    assert len(result[0].timeframe) > 0



def test_recommendation_text():

    result = RecommendationService().generate(

        replacement_shortage=True

    )

    assert len(result[0].recommendation) > 0
'@ | Set-Content `
"tests\core\test_farm_recommendation_engine.py"


Write-Host "HERD-028 Farm Command Center Recommendation Engine Build Complete"