from enum import Enum



class AutonomyEventType(str, Enum):

    RECOMMENDATION_CREATED = (
        "recommendation_created"
    )

    ACTION_APPROVED = (
        "action_approved"
    )

    ACTION_EXECUTED = (
        "action_executed"
    )

    OUTCOME_RECORDED = (
        "outcome_recorded"
    )

    LEARNING_UPDATED = (
        "learning_updated"
    )

