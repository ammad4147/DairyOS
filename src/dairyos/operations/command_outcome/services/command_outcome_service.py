from datetime import datetime

from ..models.command_outcome import CommandOutcome
from ..models.outcome_status import OutcomeStatus


class CommandOutcomeService:
    """
    Creates operational outcomes.
    """


    def record_outcome(
        self,
        outcome_id,
        command_id,
        impact_score,
        notes,
    ):

        if impact_score >= 80:

            status = OutcomeStatus.SUCCESSFUL

        elif impact_score >= 50:

            status = OutcomeStatus.PARTIAL

        else:

            status = OutcomeStatus.UNSUCCESSFUL


        return CommandOutcome(
            outcome_id=outcome_id,
            command_id=command_id,
            impact_score=impact_score,
            status=status,
            notes=notes,
            created_at=datetime.now(),
        )
