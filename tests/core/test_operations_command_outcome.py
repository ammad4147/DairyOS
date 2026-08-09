from dairyos.operations.command_outcome.services.command_outcome_service import (
    CommandOutcomeService,
)

from dairyos.operations.command_outcome.services.outcome_evaluation_service import (
    OutcomeEvaluationService,
)

from dairyos.operations.command_outcome.models.outcome_status import (
    OutcomeStatus,
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



def test_unsuccessful_outcome_requires_improvement():

    service = CommandOutcomeService()


    outcome = service.record_outcome(
        "OUT-002",
        "CMD-002",
        30,
        "Expected improvement not achieved",
    )


    evaluator = OutcomeEvaluationService()


    assert evaluator.requires_improvement(outcome) is True
