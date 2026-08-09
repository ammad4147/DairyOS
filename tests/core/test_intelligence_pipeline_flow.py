from dairyos.intelligence.integration.cross_intelligence_gateway import (
    CrossIntelligenceGateway,
)

from dairyos.intelligence.integration.intelligence_pipeline import (
    IntelligencePipeline,
)

from dairyos.intelligence.integration.connectors.decision_workflow_connector import (
    DecisionWorkflowConnector,
)

from dairyos.intelligence.integration.connectors.workflow_execution_connector import (
    WorkflowExecutionConnector,
)

from dairyos.intelligence.integration.connectors.learning_memory_connector import (
    LearningMemoryConnector,
)


def test_complete_intelligence_pipeline_flow():

    gateway = CrossIntelligenceGateway()

    pipeline = IntelligencePipeline(
        gateway=gateway,
    )

    decision_connector = DecisionWorkflowConnector()

    workflow_result = decision_connector.submit(
        "decision-001"
    )

    execution_connector = WorkflowExecutionConnector()

    execution_result = execution_connector.dispatch(
        workflow_result["decision"]
    )

    memory_connector = LearningMemoryConnector()

    memory_result = memory_connector.store(
        execution_result["workflow"]
    )


    assert pipeline.status()["status"] == "initialized"

    assert workflow_result["status"] == "submitted"

    assert execution_result["status"] == "dispatched"

    assert memory_result["status"] == "stored"
