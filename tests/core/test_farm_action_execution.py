from dairyos.herd.dashboard.services.action_execution_service import ActionExecutionService
from dairyos.herd.dashboard.models.recommendation import Recommendation



def test_action_creation():

    recommendation = Recommendation(

        "REPRODUCTION",

        "Open cows",

        "Review breeding performance",

        "MEDIUM",

        "14 days"

    )


    action = ActionExecutionService().create_action(recommendation)


    assert action.status == "OPEN"



def test_action_assignment():

    recommendation = Recommendation(

        "HEALTH",

        "Health issue",

        "Review treatment",

        "HIGH",

        "7 days"

    )


    action = ActionExecutionService().create_action(recommendation)


    assert action.assigned_to == "Farm Manager"



def test_action_priority():

    recommendation = Recommendation(

        "HERD",

        "Replacement shortage",

        "Secure animals",

        "HIGH",

        "30 days"

    )


    action = ActionExecutionService().create_action(recommendation)


    assert action.priority == "HIGH"



def test_action_completion():

    recommendation = Recommendation(

        "HEALTH",

        "Vaccination",

        "Complete vaccination",

        "MEDIUM",

        "7 days"

    )


    service = ActionExecutionService()


    action = service.create_action(recommendation)


    service.complete_action(action)


    assert action.completed is True



def test_completed_status():

    recommendation = Recommendation(

        "FINANCE",

        "Cost issue",

        "Review expenses",

        "MEDIUM",

        "14 days"

    )


    service = ActionExecutionService()


    action = service.create_action(recommendation)


    service.complete_action(action)


    assert action.status == "COMPLETED"



def test_action_queue():

    recommendations = [

        Recommendation(

            "HEALTH",

            "Alert",

            "Check animal",

            "HIGH",

            "7 days"

        )

    ]


    actions = ActionExecutionService().action_queue(recommendations)


    assert len(actions) == 1



def test_queue_action_status():

    recommendations = [

        Recommendation(

            "HERD",

            "Issue",

            "Review",

            "MEDIUM",

            "14 days"

        )

    ]


    actions = ActionExecutionService().action_queue(recommendations)


    assert actions[0].status == "OPEN"



def test_action_category():

    recommendation = Recommendation(

        "PRODUCTION",

        "Milk drop",

        "Investigate production",

        "MEDIUM",

        "7 days"

    )


    action = ActionExecutionService().create_action(recommendation)


    assert action.category == "PRODUCTION"



def test_action_timeframe():

    recommendation = Recommendation(

        "FINANCE",

        "Cost",

        "Control cost",

        "MEDIUM",

        "14 days"

    )


    action = ActionExecutionService().create_action(recommendation)


    assert action.timeframe == "14 days"



def test_default_assignment():

    recommendation = Recommendation(

        "HERD",

        "Issue",

        "Review",

        "LOW",

        "30 days"

    )


    action = ActionExecutionService().create_action(recommendation)


    assert action.assigned_to == "Farm Manager"
