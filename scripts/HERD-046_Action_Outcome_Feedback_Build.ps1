$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-046 Action Outcome Feedback Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class ActionOutcome:


    action: str

    status: str

    result: str

    outcome: str

    learning: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\action_outcome.py"



@'
from ..models.action_outcome import ActionOutcome



class ActionOutcomeService:



    def evaluate(

        self,

        action,

        completed,

        improvement

    ):


        if completed and improvement:

            status = "COMPLETED"

            outcome = "SUCCESS"

            learning = (

                f"{action} improved farm condition"

            )


        elif completed:

            status = "COMPLETED"

            outcome = "NO IMPROVEMENT"

            learning = (

                f"{action} requires review"

            )


        else:

            status = "PENDING"

            outcome = "UNKNOWN"

            learning = (

                "Action execution required"

            )



        return ActionOutcome(

            action,

            status,

            self._result(outcome),

            outcome,

            learning

        )



    def _result(

        self,

        outcome

    ):


        results = {

            "SUCCESS":

                "Condition improved",

            "NO IMPROVEMENT":

                "Further analysis required",

            "UNKNOWN":

                "Awaiting execution"

        }


        return results.get(

            outcome,

            "Review"

        )



    def successful(

        self,

        outcome

    ):


        return outcome.outcome == "SUCCESS"
'@ | Set-Content `
"dairyos\herd\dashboard\services\action_outcome_service.py"



@'
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
'@ | Set-Content `
"tests\core\test_action_outcome.py"



Write-Host "HERD-046 Action Outcome Feedback Build Complete"