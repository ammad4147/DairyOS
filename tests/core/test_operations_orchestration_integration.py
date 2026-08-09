from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)

from dairyos.intelligence.operations.orchestration.services.operations_orchestration_service import (
    OperationsOrchestrationService,
)

from dairyos.intelligence.operations.orchestration.repository.adapters.operations_orchestration_repository import (
    OperationsOrchestrationRepository,
)

from dairyos.intelligence.operations.orchestration.integration.operations_orchestration_integration import (
    OperationsOrchestrationIntegration,
)



def test_process_and_complete_action():

    service = OperationsOrchestrationService()

    repository = OperationsOrchestrationRepository()

    integration = OperationsOrchestrationIntegration(
        service,
        repository,
    )


    action = OperationalAction(
        action_type="health_check",
        description="Inspect low activity cows",
        priority="medium",
        status="generated",
        source_decision="health_intelligence_engine",
    )


    assignment = integration.process_action(
        action,
        "farm_manager",
        "operations",
    )


    assert assignment.assigned_to == "farm_manager"
    assert len(repository.get_actions()) == 1
    assert len(repository.get_assignments()) == 1



    outcome = integration.complete_action(
        action,
        "farm_manager",
        "Inspection completed",
        "Animal checks completed",
        True,
        "No major issue found",
    )


    assert outcome.success is True
    assert len(repository.get_executions()) == 1
    assert len(repository.get_outcomes()) == 1
