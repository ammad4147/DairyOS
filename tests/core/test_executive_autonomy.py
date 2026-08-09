from dairyos.herd.dashboard.services.executive_autonomy_service import ExecutiveAutonomyService



def test_issue_saved():

    brief = ExecutiveAutonomyService().generate_brief(

        "Milk production variance detected"

    )

    assert brief.key_issue == "Milk production variance detected"



def test_status():

    brief = ExecutiveAutonomyService().generate_brief(

        "Milk production variance"

    )

    assert brief.farm_status == "STABLE"



def test_risk_level():

    brief = ExecutiveAutonomyService().generate_brief(

        "Milk production variance"

    )

    assert brief.risk_level == "MEDIUM"



def test_focus():

    brief = ExecutiveAutonomyService().generate_brief(

        "Milk production variance"

    )

    assert brief.recommended_focus == "Feed efficiency review"



def test_owner_action():

    brief = ExecutiveAutonomyService().generate_brief(

        "Milk production variance"

    )

    assert "ration" in brief.owner_action.lower()



def test_expected_impact():

    brief = ExecutiveAutonomyService().generate_brief(

        "Milk production variance"

    )

    assert "Production" in brief.expected_impact



def test_general_status():

    brief = ExecutiveAutonomyService().generate_brief(

        "Routine observation"

    )

    assert brief.farm_status == "STABLE"



def test_general_risk():

    brief = ExecutiveAutonomyService().generate_brief(

        "Routine observation"

    )

    assert brief.risk_level == "LOW"



def test_general_focus():

    brief = ExecutiveAutonomyService().generate_brief(

        "Routine observation"

    )

    assert brief.recommended_focus == "Routine monitoring"



def test_brief_generation():

    brief = ExecutiveAutonomyService().generate_brief(

        "Farm condition"

    )

    assert brief.owner_action is not None
