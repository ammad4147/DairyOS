from dairyos.herd.dashboard.services.preventive_action_service import PreventiveActionService



def test_plan_creation():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "HIGH"

    )

    assert plan.category == "PRODUCTION"



def test_high_priority():

    plan = PreventiveActionService().create_plan(

        "HEALTH",

        "HIGH"

    )

    assert plan.priority == "HIGH"



def test_critical_priority():

    plan = PreventiveActionService().create_plan(

        "FINANCE",

        "CRITICAL"

    )

    assert plan.priority == "URGENT"



def test_low_priority():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "LOW"

    )

    assert plan.priority == "LOW"



def test_owner_attention():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "HIGH"

    )

    assert plan.owner_attention



def test_no_owner_attention():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "LOW"

    )

    assert not plan.owner_attention



def test_production_actions():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "HIGH"

    )

    assert "Review feed quality" in plan.actions



def test_health_actions():

    plan = PreventiveActionService().create_plan(

        "HEALTH",

        "HIGH"

    )

    assert "Review animal health status" in plan.actions



def test_timeline():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "HIGH"

    )

    assert plan.timeline == "Within 7 days"



def test_model():

    plan = PreventiveActionService().create_plan(

        "FINANCE",

        "MEDIUM"

    )

    assert plan.risk_level == "MEDIUM"
