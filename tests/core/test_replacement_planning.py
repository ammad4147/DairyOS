from dairyos.herd.replacement.services.replacement_planning_service import ReplacementPlanningService



def test_current_cows():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.current_lactating_cows == 25



def test_culling_rate():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.culling_rate == 0.15



def test_required_replacements():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.required_replacements == 3



def test_available_heifers():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.available_heifers == 8



def test_secure_status():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.status == "SECURE"



def test_secure_action():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.action == "Continue development program"



def test_shortage_status():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        2

    )

    assert result.status == "SHORTAGE"



def test_shortage_action():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        2

    )

    assert result.action == "Increase replacement planning"



def test_growth_scenario():

    result = ReplacementPlanningService().evaluate(

        50,

        0.15,

        10

    )

    assert result.required_replacements == 7



def test_replacement_flow():

    result = ReplacementPlanningService().evaluate(

        25,

        0.15,

        8

    )

    assert result.status == "SECURE"
