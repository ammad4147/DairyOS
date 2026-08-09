$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-056 Operational Outcome Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class OperationalOutcome:


    action: str

    result: str

    success: bool

    learning_note: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\operational_outcome.py"



@'
from ..models.operational_outcome import OperationalOutcome



class OperationalOutcomeService:



    def evaluate(

        self,

        action,

        result

    ):


        success = (

            "improved" in result.lower()

            or "success" in result.lower()

        )


        if success:

            learning = (

                "Increase confidence for future interventions"

            )

        else:

            learning = (

                "Review intervention effectiveness"

            )


        return OperationalOutcome(

            action,

            result,

            success,

            learning

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\operational_outcome_service.py"



@'
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
'@ | Set-Content `
"tests\core\test_operational_outcome.py"



Write-Host "HERD-056 Operational Outcome Build Complete"