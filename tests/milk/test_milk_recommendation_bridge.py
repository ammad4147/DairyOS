from dairyos.milk.integration import (
    MilkRecommendationBridge,
)


from dairyos.intelligence.command.models.farm_situation import (
    FarmSituation,
)


from dairyos.intelligence.command.repository.adapters.memory_recommendation_repository import (
    MemoryRecommendationRepository,
)



def test_milk_normal_recommendation():

    situation = FarmSituation(

        situation_id="MILK-NORMAL",

        farm_id="FARM-001",

        status="NORMAL",

        priority="LOW",

    )


    recommendation = MilkRecommendationBridge().create_recommendation(

        situation,

        MemoryRecommendationRepository(),

    )


    assert recommendation.urgency == "LOW"



def test_milk_warning_recommendation():

    situation = FarmSituation(

        situation_id="MILK-WARNING",

        farm_id="FARM-001",

        status="WARNING",

        priority="MEDIUM",

    )


    recommendation = MilkRecommendationBridge().create_recommendation(

        situation,

        MemoryRecommendationRepository(),

    )


    assert recommendation.urgency == "MEDIUM"

    assert (
        "Investigate milk production decline"
        in recommendation.action
    )



def test_milk_critical_recommendation():

    situation = FarmSituation(

        situation_id="MILK-CRITICAL",

        farm_id="FARM-001",

        status="CRITICAL",

        priority="HIGH",

    )


    recommendation = MilkRecommendationBridge().create_recommendation(

        situation,

        MemoryRecommendationRepository(),

    )


    assert recommendation.urgency == "HIGH"

    assert (
        "Immediate investigation required"
        in recommendation.action
    )
