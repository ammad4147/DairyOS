from dairyos.herd.dashboard.services.operational_outcome_service import OperationalOutcomeService



def test_outcome_creation():

    outcome = OperationalOutcomeService().evaluate(

        "Feed Investigation",

        "Milk production improved"

    )

    assert outcome.action == "Feed Investigation"



def test_result_saved():

    outcome = OperationalOutcomeService().evaluate(

        "Health Review",

        "Animal condition improved"

    )

    assert outcome.result == "Animal condition improved"



def test_success_detection():

    outcome = OperationalOutcomeService().evaluate(

        "Feed Investigation",

        "Milk production improved"

    )

    assert outcome.success



def test_failed_detection():

    outcome = OperationalOutcomeService().evaluate(

        "Feed Investigation",

        "No improvement observed"

    )

    assert not outcome.success



def test_success_learning():

    outcome = OperationalOutcomeService().evaluate(

        "Feed Investigation",

        "Success achieved"

    )

    assert "Increase confidence" in outcome.learning_note



def test_failure_learning():

    outcome = OperationalOutcomeService().evaluate(

        "Feed Investigation",

        "Failed intervention"

    )

    assert "Review" in outcome.learning_note



def test_action_field():

    outcome = OperationalOutcomeService().evaluate(

        "Health Review",

        "Success"

    )

    assert outcome.action == "Health Review"



def test_model_boolean():

    outcome = OperationalOutcomeService().evaluate(

        "Action",

        "Success"

    )

    assert isinstance(outcome.success, bool)



def test_model_learning():

    outcome = OperationalOutcomeService().evaluate(

        "Action",

        "Success"

    )

    assert isinstance(outcome.learning_note, str)



def test_closed_loop_flow():

    service = OperationalOutcomeService()

    outcome = service.evaluate(

        "Feed Investigation",

        "Milk production improved"

    )

    assert outcome.success
