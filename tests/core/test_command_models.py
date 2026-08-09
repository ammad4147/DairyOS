from dairyos.intelligence.command.models.command_action import (
    CommandAction,
)

from dairyos.intelligence.command.models.farm_situation import (
    FarmSituation,
)

from dairyos.intelligence.command.models.operational_recommendation import (
    OperationalRecommendation,
)


def test_command_action_creation():

    action = CommandAction(
        action_id="a1",
        recommendation_id="r1",
        action_type="feed_adjustment",
        status="pending",
    )

    assert action.action_id == "a1"
    assert action.status == "pending"



def test_farm_situation_creation():

    situation = FarmSituation(
        situation_id="s1",
        farm_id="farm1",
        status="attention_required",
        priority="high",
    )

    assert situation.situation_id == "s1"
    assert situation.priority == "high"



def test_operational_recommendation_creation():

    recommendation = OperationalRecommendation(
        recommendation_id="r1",
        situation_id="s1",
        action="increase_monitoring",
        urgency="medium",
    )

    assert recommendation.recommendation_id == "r1"
    assert recommendation.urgency == "medium"
