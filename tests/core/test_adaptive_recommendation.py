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
