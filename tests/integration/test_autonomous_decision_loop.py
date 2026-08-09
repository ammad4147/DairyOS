"""
DairyOS Sprint 025

Autonomous Decision Loop Validation

Signal
 -> Decision
 -> Recommendation
 -> Command
 -> Workflow
 -> Execution
"""
    

def test_autonomous_decision_loop_components():

    from dairyos.intelligence.decision.services.decision_service import (
        DecisionService,
    )

    from dairyos.intelligence.command.services.recommendation_service import (
        RecommendationService,
    )

    from dairyos.intelligence.command.services.command_execution_service import (
        CommandExecutionService,
    )

    from dairyos.intelligence.workflow.gateway.workflow_gateway import (
        WorkflowGateway,
    )

    from dairyos.intelligence.execution.gateway.execution_gateway import (
        ExecutionGateway,
    )


    assert DecisionService is not None
    assert RecommendationService is not None
    assert CommandExecutionService is not None
    assert WorkflowGateway is not None
    assert ExecutionGateway is not None
