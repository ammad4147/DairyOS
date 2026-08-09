from dairyos.intelligence.operations.orchestration.models.action_outcome import (
    ActionOutcome,
)


class OutcomeProcessor:
    """
    Processes operational action outcomes
    for intelligence feedback.
    """

    def process(
        self,
        action_type: str,
        result: str,
        success: bool,
        feedback: str = "",
    ) -> ActionOutcome:

        return ActionOutcome(
            action_type=action_type,
            result=result,
            success=success,
            feedback=feedback,
        )
