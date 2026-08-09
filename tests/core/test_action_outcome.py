from dairyos.herd.dashboard.services.action_outcome_service import ActionOutcomeService



def test_successful_outcome():

    outcome = ActionOutcomeService().evaluate(

        "Review feed quality",

        True,

        True

    )

    assert outcome.outcome == "SUCCESS"



def test_completed_without_improvement():

    outcome = ActionOutcomeService().evaluate(

        "Health review",

        True,

        False

    )

    assert outcome.outcome == "NO IMPROVEMENT"



def test_pending_action():

    outcome = ActionOutcomeService().evaluate(

        "Review records",

        False,

        False

    )

    assert outcome.status == "PENDING"



def test_success_result():

    outcome = ActionOutcomeService().evaluate(

        "Feed review",

        True,

        True

    )

    assert outcome.result == "Condition improved"



def test_failure_result():

    outcome = ActionOutcomeService().evaluate(

        "Health review",

        True,

        False

    )

    assert outcome.result == "Further analysis required"



def test_learning_created():

    outcome = ActionOutcomeService().evaluate(

        "Feed review",

        True,

        True

    )

    assert "improved" in outcome.learning



def test_success_check():

    service = ActionOutcomeService()

    outcome = service.evaluate(

        "Feed review",

        True,

        True

    )

    assert service.successful(outcome)



def test_unsuccessful_check():

    service = ActionOutcomeService()

    outcome = service.evaluate(

        "Feed review",

        False,

        False

    )

    assert not service.successful(outcome)



def test_action_saved():

    outcome = ActionOutcomeService().evaluate(

        "Production review",

        True,

        True

    )

    assert outcome.action == "Production review"



def test_model():

    outcome = ActionOutcomeService().evaluate(

        "Review",

        True,

        True

    )

    assert outcome.status == "COMPLETED"
