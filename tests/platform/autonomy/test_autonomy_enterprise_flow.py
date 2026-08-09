from dairyos.platform.autonomy.orchestration.services.autonomy_orchestrator import (
    AutonomyOrchestrator,
)


from dairyos.platform.autonomy.copilot.services.farm_copilot import (
    FarmCopilot,
)


from dairyos.platform.autonomy.governance.services.autonomy_governance import (
    AutonomyGovernance,
)


from dairyos.platform.autonomy.execution.services.execution_service import (
    ExecutionService,
)


from dairyos.platform.autonomy.audit.services.autonomy_audit_service import (
    AutonomyAuditService,
)


from dairyos.platform.autonomy.learning.services.autonomy_learning_service import (
    AutonomyLearningService,
)



def test_autonomous_enterprise_flow():


    orchestrator = AutonomyOrchestrator()


    analysis = orchestrator.analyze(

        problem="Milk production decline",

        evidence=[

            "Lower yield",

            "Health deviation",

        ],

        impact="Potential production loss",

        confidence=0.88,

    )


    assert analysis["context"].confidence == 0.88



    recommendation = analysis["recommendation"]


    assert recommendation.priority == "high"



    copilot = FarmCopilot()


    response = copilot.respond(

        "What requires attention?",

        [recommendation],

    )


    assert response.message



    governance = AutonomyGovernance()


    check = governance.evaluate(

        confidence=0.88,

        risk_level="medium",

    )


    assert check.allowed is True



    execution = ExecutionService()


    plan = execution.create_plan(

        title="Review health conditions",

        description="Inspect affected animals",

        assigned_to="veterinarian",

        priority="high",

    )


    execution.approve(plan)


    execution.complete(plan)


    assert plan.status == "completed"



    audit = AutonomyAuditService()


    event = audit.record(

        event_type="action_executed",

        entity_type="animal_group",

        entity_id="group_a",

        actor="manager",

        details={

            "recommendation":

            "health review"

        },

    )


    assert event.event_type == "action_executed"



    learning = AutonomyLearningService()


    signal = learning.record(

        recommendation_id="rec-001",

        outcome="successful",

        confidence_change=0.04,

    )


    assert signal.confidence_change == 0.04

