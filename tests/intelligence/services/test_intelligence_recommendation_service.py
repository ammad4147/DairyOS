from dairyos.intelligence.services.intelligence_recommendation_service import (
    IntelligenceRecommendationService,
)

from dairyos.intelligence.models.intelligence_signal import (
    IntelligenceSignal,
)



def test_recommendation_generated_from_signal():

    service = IntelligenceRecommendationService()


    signal = IntelligenceSignal(

        signal_type=
            "MILK_PRODUCTION_VARIANCE",

        severity=
            "WARNING",

        source=
            "milk",

        message=
            "Milk production below expected",

    )


    analysis = {

        "priority":
            "MEDIUM"

    }


    result = service.generate(

        analysis,

        [signal],

    )


    assert len(result) == 1

    assert result[0].recommendation_type == (
        "PRODUCTION_REVIEW"
    )

    assert result[0].priority == (
        "MEDIUM"
    )



def test_unknown_signal_generates_review():

    service = IntelligenceRecommendationService()


    signal = IntelligenceSignal(

        signal_type=
            "UNKNOWN_EVENT",

        severity=
            "WARNING",

        source=
            "operations",

    )


    result = service.generate(

        {
            "priority":
                "LOW"
        },

        [signal],

    )


    assert result[0].recommendation_type == (
        "OPERATIONAL_REVIEW"
    )
