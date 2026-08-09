$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-048 Adaptive Recommendation Engine Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class AdaptiveRecommendation:


    category: str

    recommended_action: str

    confidence: int

    reason: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\adaptive_recommendation.py"



@'
from ..models.adaptive_recommendation import AdaptiveRecommendation



class AdaptiveRecommendationService:



    def recommend(

        self,

        category,

        actions

    ):


        if not actions:

            return AdaptiveRecommendation(

                category,

                "No recommendation available",

                0,

                "No historical evidence"

            )


        best_action = max(

            actions,

            key=lambda x: x["success_rate"]

        )


        confidence = best_action["success_rate"]



        return AdaptiveRecommendation(

            category,

            best_action["action"],

            confidence,

            "Highest historical success rate"

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\adaptive_recommendation_service.py"



@'
from dairyos.herd.dashboard.services.adaptive_recommendation_service import AdaptiveRecommendationService



def test_recommendation_creation():

    result = AdaptiveRecommendationService().recommend(

        "PRODUCTION",

        [

            {

                "action": "Feed review",

                "success_rate": 85

            }

        ]

    )

    assert result.category == "PRODUCTION"



def test_highest_success_selected():

    result = AdaptiveRecommendationService().recommend(

        "PRODUCTION",

        [

            {

                "action": "Health review",

                "success_rate": 60

            },

            {

                "action": "Feed review",

                "success_rate": 85

            }

        ]

    )

    assert result.recommended_action == "Feed review"



def test_confidence():

    result = AdaptiveRecommendationService().recommend(

        "PRODUCTION",

        [

            {

                "action": "Feed review",

                "success_rate": 85

            }

        ]

    )

    assert result.confidence == 85



def test_reason():

    result = AdaptiveRecommendationService().recommend(

        "PRODUCTION",

        [

            {

                "action": "Feed review",

                "success_rate": 85

            }

        ]

    )

    assert result.reason == "Highest historical success rate"



def test_multiple_actions():

    result = AdaptiveRecommendationService().recommend(

        "HEALTH",

        [

            {

                "action": "Vaccination review",

                "success_rate": 90

            },

            {

                "action": "Observation",

                "success_rate": 40

            }

        ]

    )

    assert result.recommended_action == "Vaccination review"



def test_empty_actions():

    result = AdaptiveRecommendationService().recommend(

        "FINANCE",

        []

    )

    assert result.confidence == 0



def test_action_text():

    result = AdaptiveRecommendationService().recommend(

        "PRODUCTION",

        [

            {

                "action": "Feed review",

                "success_rate": 80

            }

        ]

    )

    assert result.recommended_action == "Feed review"



def test_zero_success():

    result = AdaptiveRecommendationService().recommend(

        "FINANCE",

        [

            {

                "action": "Review",

                "success_rate": 0

            }

        ]

    )

    assert result.confidence == 0



def test_category_preserved():

    result = AdaptiveRecommendationService().recommend(

        "REPRODUCTION",

        [

            {

                "action": "Breeding review",

                "success_rate": 75

            }

        ]

    )

    assert result.category == "REPRODUCTION"



def test_model():

    result = AdaptiveRecommendationService().recommend(

        "HEALTH",

        [

            {

                "action": "Health review",

                "success_rate": 70

            }

        ]

    )

    assert result.confidence == 70
'@ | Set-Content `
"tests\core\test_adaptive_recommendation.py"



Write-Host "HERD-048 Adaptive Recommendation Engine Build Complete"