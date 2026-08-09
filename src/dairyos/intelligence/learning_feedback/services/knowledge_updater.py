from dairyos.intelligence.learning_feedback.models.knowledge_adjustment import (
    KnowledgeAdjustment,
)


class KnowledgeUpdater:
    """
    Updates intelligence knowledge.

    Future extensions:

    - automatic calibration
    - policy tuning
    """


    def update(
        self,
        decision_area: str,
        previous_value: str,
        new_value: str,
        reason: str,
    ) -> KnowledgeAdjustment:

        return KnowledgeAdjustment(
            decision_area=decision_area,
            previous_value=previous_value,
            new_value=new_value,
            reason=reason,
        )
