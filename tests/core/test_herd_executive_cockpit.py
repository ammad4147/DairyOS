from dairyos.herd.dashboard.models.herd_command import HerdCommand

from dairyos.herd.dashboard.services.executive_cockpit_service import ExecutiveCockpitService



def command():


    return HerdCommand(

        farm_name="Trident Dairies",

        total_animals=100,

        production_status="ACTIVE",

        health_status="NORMAL",

        reproduction_status="NORMAL",

        financial_status="POSITIVE",

        overall_risk="LOW",

        owner_attention="",

    )



def test_cockpit_creation():

    cockpit = ExecutiveCockpitService().generate(

        command()

    )

    assert cockpit.farm_name == "Trident Dairies"



def test_health_score():

    service = ExecutiveCockpitService()

    assert service.calculate_health_score(0) == 100



def test_reproduction_score():

    service = ExecutiveCockpitService()

    assert service.calculate_reproduction_score(8) == 50



def test_finance_score():

    service = ExecutiveCockpitService()

    assert service.calculate_financial_score("WARNING") == 70



def test_replacement_score():

    service = ExecutiveCockpitService()

    assert service.calculate_replacement_score(True) == 50



def test_overall_score():

    cockpit = ExecutiveCockpitService().generate(

        command()

    )

    assert cockpit.overall_score == 100



def test_high_risk_summary():

    cmd = command()

    cmd.overall_risk = "HIGH"

    cmd.owner_attention = "Review replacement pipeline"

    cmd.recommended_actions = [

        "Review replacement pipeline"

    ]

    cockpit = ExecutiveCockpitService().generate(

        cmd,

        replacement_shortage=True

    )

    assert cockpit.risk_level == "HIGH"



def test_command_to_cockpit_flow():

    cockpit = ExecutiveCockpitService().generate(

        command(),

        health_alerts=1,

        open_cows=4

    )

    assert cockpit.health_score == 80

    assert cockpit.reproduction_score == 75
