from dairyos.intelligence.integration.connectors.workflow_execution_connector import (
    WorkflowExecutionConnector,
)


def test_workflow_execution_connector():

    connector = WorkflowExecutionConnector()

    result = connector.dispatch(
        "workflow-001"
    )

    assert result["workflow"] == "workflow-001"
    assert result["status"] == "dispatched"
