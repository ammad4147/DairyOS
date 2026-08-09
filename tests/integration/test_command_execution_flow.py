"""
DairyOS Sprint 025

Command to Execution Validation

Command
 ?
Workflow
 ?
Execution
"""


def test_command_execution_components():

    from dairyos.intelligence.command.gateway.command_gateway import (
        CommandGateway,
    )

    from dairyos.intelligence.command.integration.command_intelligence_bridge import (
        CommandIntelligenceBridge,
    )

    from dairyos.intelligence.workflow.gateway.workflow_gateway import (
        WorkflowGateway,
    )

    from dairyos.intelligence.execution.gateway.execution_gateway import (
        ExecutionGateway,
    )


    assert CommandGateway is not None
    assert CommandIntelligenceBridge is not None
    assert WorkflowGateway is not None
    assert ExecutionGateway is not None
