from dairyos.operations.command_outcome.models.outcome_status import (
    OutcomeStatus,
)
from dairyos.operations.command_outcome.services.command_outcome_service import (
    CommandOutcomeService,
)


def test_successful_command_outcome():

    service = CommandOutcomeService()


    outcome = service.record_outcome(
        "OUT-001",
        "CMD-001",
        90,
        "Health improvement achieved",
    )


    assert outcome.status == OutcomeStatus.SUCCESSFUL
