from ..models.closure_status import ClosureStatus
from ..models.operational_closure import OperationalClosure

from dairyos.operations.command_verification.models.verification_status import (
    VerificationStatus,
)

from dairyos.operations.command_outcome.models.outcome_status import (
    OutcomeStatus,
)

from datetime import datetime


class ClosureIntegrationService:
    """
    Integrates verification and outcome
    information into closure readiness.

    This service evaluates closure state.

    It does not:
    - automatically close records
    - bypass human review
    - mutate execution state
    """


    def evaluate(
        self,
        closure_id: str,
        resolution_reference: str,
        reviewed_by: str,
        verification,
        outcome,
    ) -> OperationalClosure:


        if (
            verification.status
            == VerificationStatus.VERIFIED
            and
            outcome.status
            == OutcomeStatus.SUCCESSFUL
        ):

            status = ClosureStatus.REVIEW


        elif (
            verification.status
            == VerificationStatus.FAILED
        ):

            status = ClosureStatus.OPEN


        else:

            status = ClosureStatus.REVIEW



        return OperationalClosure(

            closure_id=closure_id,

            resolution_reference=resolution_reference,

            reviewed_by=reviewed_by,

            effectiveness_score=(
                outcome.impact_score
            ),

            created_at=datetime.now(),

            status=status,

        )
