from dairyos.herd.dashboard.services.autonomous_decision_agent_service import AutonomousDecisionAgentService



def test_condition_saved():

    decision = AutonomousDecisionAgentService().decide(

        "Milk yield dropped"

    )

    assert decision.condition == "Milk yield dropped"



def test_recommended_action():

    decision = AutonomousDecisionAgentService().decide(

        "Milk production decline"

    )

    assert decision.recommended_action == "Feed Investigation"



def test_confidence():

    decision = AutonomousDecisionAgentService().decide(

        "Milk decline"

    )

    assert decision.confidence == 87



def test_priority():

    decision = AutonomousDecisionAgentService().decide(

        "Milk decline"

    )

    assert decision.priority == "HIGH"



def test_workflow_steps():

    decision = AutonomousDecisionAgentService().decide(

        "Milk decline"

    )

    assert len(decision.workflow_steps) == 3



def test_ration_step():

    decision = AutonomousDecisionAgentService().decide(

        "Production decline"

    )

    assert "Review ration" in decision.workflow_steps



def test_health_step():

    decision = AutonomousDecisionAgentService().decide(

        "Production decline"

    )

    assert "Check health" in decision.workflow_steps



def test_environment_step():

    decision = AutonomousDecisionAgentService().decide(

        "Production decline"

    )

    assert "Verify environment" in decision.workflow_steps



def test_general_decision():

    decision = AutonomousDecisionAgentService().decide(

        "Routine observation"

    )

    assert decision.recommended_action == "General Review"



def test_agent_flow():

    decision = AutonomousDecisionAgentService().decide(

        "Milk production dropped"

    )

    assert decision.priority == "HIGH"
