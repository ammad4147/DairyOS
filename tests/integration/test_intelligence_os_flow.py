"""
DairyOS Enterprise Integration Validation

Sprint 025 Step 01

Validates that all major intelligence domains
are available as one operating system layer.

Validation scope:

Kernel
Decision
Command
Workflow
Execution
Memory
Learning
Knowledge
Prediction
Production
"""
    

def test_intelligence_os_domain_imports():

    from dairyos.intelligence.kernel.services.intelligence_kernel import (
        IntelligenceKernel,
    )

    from dairyos.intelligence.decision.services.decision_service import (
        DecisionService,
    )

    from dairyos.intelligence.command.services.command_orchestrator import (
        CommandOrchestrator,
    )

    from dairyos.intelligence.workflow.gateway.workflow_gateway import (
        WorkflowGateway,
    )

    from dairyos.intelligence.execution.gateway.execution_gateway import (
        ExecutionGateway,
    )

    from dairyos.intelligence.memory.gateway.memory_gateway import (
        MemoryGateway,
    )

    from dairyos.intelligence.learning.gateway.learning_gateway import (
        LearningGateway,
    )

    from dairyos.intelligence.knowledge.gateway.knowledge_gateway import (
        KnowledgeGateway,
    )

    from dairyos.intelligence.prediction.gateway.prediction_gateway import (
        PredictionGateway,
    )


    assert IntelligenceKernel is not None
    assert DecisionService is not None
    assert CommandOrchestrator is not None
    assert WorkflowGateway is not None
    assert ExecutionGateway is not None
    assert MemoryGateway is not None
    assert LearningGateway is not None
    assert KnowledgeGateway is not None
    assert PredictionGateway is not None
