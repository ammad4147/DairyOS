from dairyos.herd.dashboard.models.herd_command import HerdCommand

from dairyos.herd.dashboard.services.command_decision_service import CommandDecisionService

from dairyos.herd.dashboard.services.herd_command_service import HerdCommandService

from dairyos.herd.intelligence.models.herd_decision import HerdDecision



class Context:


    farm_name = "Trident Dairies"

    total_animals = 100

    health_alerts = 2

    open_cows = 5

    replacement_shortage = True

    production_status = "ACTIVE"

    financial_status = "WARNING"



def test_command_decision_creation():

    command = HerdCommand(

        "Farm",

        10,

        "ACTIVE",

        "NORMAL",

        "NORMAL",

        "POSITIVE",

        "LOW",

        ""

    )

    assert command.decision_score == 0



def test_decision_bridge():

    command = HerdCommandService().generate(

        "Farm",

        10

    )


    decision = HerdDecision(

        "HIGH",

        True,

        ["Review health"],

        "URGENT",

        80

    )


    result = CommandDecisionService().apply_decision(

        command,

        decision

    )


    assert result.decision_score == 80



def test_high_priority_command():

    decision = HerdDecision(

        "HIGH",

        True,

        ["Action"],

        "URGENT",

        90

    )


    assert decision.priority_level == "URGENT"



def test_low_priority_command():

    decision = HerdDecision(

        "LOW",

        False,

        [],

        "NORMAL",

        0

    )


    assert decision.risk_level == "LOW"



def test_command_contains_actions():

    command = HerdCommandService().generate(

        "Farm",

        10

    )


    decision = HerdDecision(

        "MEDIUM",

        True,

        ["Check health"],

        "HIGH",

        30

    )


    result = CommandDecisionService().apply_decision(

        command,

        decision

    )


    assert len(result.recommended_actions) == 1



def test_command_score():

    decision = HerdDecision(

        "MEDIUM",

        True,

        [],

        "HIGH",

        30

    )


    assert decision.decision_score == 30



def test_context_to_command_flow():

    decision = HerdDecision(

        "HIGH",

        True,

        ["Review replacement"],

        "URGENT",

        70

    )


    command = HerdCommandService().generate_from_decision(

        Context(),

        decision

    )


    assert command.overall_risk == "HIGH"



def test_full_intelligence_to_dashboard_flow():

    decision = HerdDecision(

        "HIGH",

        True,

        ["Review herd"],

        "URGENT",

        100

    )


    command = HerdCommandService().generate_from_decision(

        Context(),

        decision

    )


    assert command.decision_priority == "URGENT"

    assert command.decision_score == 100
