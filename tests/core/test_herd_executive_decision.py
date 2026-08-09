from dairyos.herd.dashboard.services.executive_decision_service import ExecutiveDecisionService

from dairyos.herd.dashboard.models.executive_alert import ExecutiveAlert



def test_executive_decision_creation():

    decision = ExecutiveDecisionService().generate(

        "Trident Dairies"

    )

    assert decision.farm_name == "Trident Dairies"



def test_replacement_decision():

    alert = ExecutiveAlert(

        category="REPLACEMENT",

        priority=1,

        severity_score=100,

        issue="Replacement shortage",

        recommended_action="Secure replacement animals"

    )


    decision = ExecutiveDecisionService().generate(

        "Trident Dairies",

        [alert]

    )


    assert decision.decision_required is True

    assert decision.priority_level == "HIGH"

    assert decision.risk_level == "HIGH"



def test_health_decision():

    alert = ExecutiveAlert(

        category="HEALTH",

        priority=2,

        severity_score=80,

        issue="Health alerts",

        recommended_action="Review animal health"

    )


    decision = ExecutiveDecisionService().generate(

        "Trident Dairies",

        [alert]

    )


    assert decision.recommended_action == "Review animal health interventions"



def test_no_decision_required():

    decision = ExecutiveDecisionService().generate(

        "Trident Dairies"

    )


    assert decision.decision_required is False
