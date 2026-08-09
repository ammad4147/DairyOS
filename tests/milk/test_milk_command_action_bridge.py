from dairyos.milk.integration import (
    MilkCommandActionBridge,
)


from dairyos.intelligence.command.models.operational_recommendation import (
    OperationalRecommendation,
)


class MemoryActionRepository:


    def __init__(self):

        self.items = []


    def save(self, action):

        self.items.append(action)

        return action



def test_milk_high_priority_action_creation():

    recommendation = OperationalRecommendation(

        recommendation_id="MILK-REC-001",

        situation_id="MILK-CRITICAL",

        action=(
            "Immediate investigation required"
        ),

        urgency="HIGH",

    )


    action = MilkCommandActionBridge().create_action(

        recommendation,

        MemoryActionRepository(),

    )


    assert (
        action.action_type
        ==
        "INVESTIGATE_MILK_DECLINE"
    )


    assert action.status == "OPEN"



def test_milk_normal_action_creation():

    recommendation = OperationalRecommendation(

        recommendation_id="MILK-REC-002",

        situation_id="MILK-NORMAL",

        action=(
            "Continue normal milk operations"
        ),

        urgency="LOW",

    )


    action = MilkCommandActionBridge().create_action(

        recommendation,

        MemoryActionRepository(),

    )


    assert (
        action.action_type
        ==
        "MONITOR_MILK_STATUS"
    )
