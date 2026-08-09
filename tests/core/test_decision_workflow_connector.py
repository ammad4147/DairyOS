from dairyos.intelligence.integration.connectors.decision_workflow_connector import (
    DecisionWorkflowConnector,
)


def test_decision_workflow_connector():

    connector = DecisionWorkflowConnector()

    result = connector.submit(
        "decision-001"
    )

    assert result["decision"] == "decision-001"
    assert result["status"] == "submitted"
