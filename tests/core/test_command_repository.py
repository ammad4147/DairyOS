from dairyos.intelligence.command.repository.adapters.memory_action_repository import (
    MemoryActionRepository,
)

from dairyos.intelligence.command.repository.adapters.memory_recommendation_repository import (
    MemoryRecommendationRepository,
)

from dairyos.intelligence.command.repository.adapters.memory_situation_repository import (
    MemorySituationRepository,
)

from dairyos.intelligence.command.models.command_action import (
    CommandAction,
)

from dairyos.intelligence.command.models.operational_recommendation import (
    OperationalRecommendation,
)

from dairyos.intelligence.command.models.farm_situation import (
    FarmSituation,
)



def test_action_repository_save():

    repository = MemoryActionRepository()

    action = CommandAction(
        action_id="a1",
        recommendation_id="r1",
        action_type="inspection",
        status="pending",
    )

    result = repository.save(action)

    assert result.action_id == "a1"



def test_recommendation_repository_save():

    repository = MemoryRecommendationRepository()

    recommendation = OperationalRecommendation(
        recommendation_id="r1",
        situation_id="s1",
        action="check_feed",
        urgency="high",
    )

    result = repository.save(recommendation)

    assert result.recommendation_id == "r1"



def test_situation_repository_save():

    repository = MemorySituationRepository()

    situation = FarmSituation(
        situation_id="s1",
        farm_id="farm1",
        status="stable",
        priority="low",
    )

    result = repository.save(situation)

    assert result.situation_id == "s1"
