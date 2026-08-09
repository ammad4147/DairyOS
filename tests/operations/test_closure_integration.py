from dairyos.operations.closure.services.closure_integration_service import (
    ClosureIntegrationService,
)

from dairyos.operations.command_verification.models.command_verification import (
    CommandVerification,
)

from dairyos.operations.command_verification.models.verification_status import (
    VerificationStatus,
)

from dairyos.operations.command_outcome.models.command_outcome import (
    CommandOutcome,
)

from dairyos.operations.command_outcome.models.outcome_status import (
    OutcomeStatus,
)

from datetime import datetime



def test_successful_execution_moves_to_closure_review():

    service = ClosureIntegrationService()


    verification = CommandVerification(

        verification_id="VER-0001",

        execution_id="EXE-0001",

        result_message="Verified",

        status=VerificationStatus.VERIFIED,

        created_at=datetime.now(),

    )


    outcome = CommandOutcome(

        outcome_id="OUT-0001",

        command_id="CMD-0001",

        impact_score=95,

        status=OutcomeStatus.SUCCESSFUL,

        notes="Completed",

        created_at=datetime.now(),

    )


    closure = service.evaluate(

        closure_id="CLS-0001",

        resolution_reference="EXE-0001",

        reviewed_by="Farm Manager",

        verification=verification,

        outcome=outcome,

    )


    assert closure.status.value == "REVIEW"

    assert closure.effectiveness_score == 95
