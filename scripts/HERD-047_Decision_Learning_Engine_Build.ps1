$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-047 Decision Learning Engine Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class DecisionLearning:


    action: str

    executions: int

    successes: int

    confidence: int

    recommendation_strength: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\decision_learning.py"



@'
from ..models.decision_learning import DecisionLearning



class DecisionLearningService:



    def analyze(

        self,

        action,

        executions,

        successes

    ):


        if executions <= 0:

            confidence = 0

        else:

            confidence = int(

                (successes / executions) * 100

            )


        if confidence >= 75:

            strength = "HIGH"

        elif confidence >= 50:

            strength = "MEDIUM"

        else:

            strength = "LOW"



        return DecisionLearning(

            action,

            executions,

            successes,

            confidence,

            strength

        )



    def preferred_action(

        self,

        learning

    ):


        return learning.recommendation_strength == "HIGH"
'@ | Set-Content `
"dairyos\herd\dashboard\services\decision_learning_service.py"



@'
from dairyos.herd.dashboard.services.decision_learning_service import DecisionLearningService



def test_learning_creation():

    learning = DecisionLearningService().analyze(

        "Feed review",

        10,

        8

    )

    assert learning.action == "Feed review"



def test_confidence_calculation():

    learning = DecisionLearningService().analyze(

        "Feed review",

        10,

        8

    )

    assert learning.confidence == 80



def test_high_strength():

    learning = DecisionLearningService().analyze(

        "Feed review",

        10,

        8

    )

    assert learning.recommendation_strength == "HIGH"



def test_medium_strength():

    learning = DecisionLearningService().analyze(

        "Health review",

        10,

        6

    )

    assert learning.recommendation_strength == "MEDIUM"



def test_low_strength():

    learning = DecisionLearningService().analyze(

        "Review",

        10,

        2

    )

    assert learning.recommendation_strength == "LOW"



def test_zero_execution():

    learning = DecisionLearningService().analyze(

        "New action",

        0,

        0

    )

    assert learning.confidence == 0



def test_success_tracking():

    learning = DecisionLearningService().analyze(

        "Feed review",

        5,

        5

    )

    assert learning.successes == 5



def test_execution_tracking():

    learning = DecisionLearningService().analyze(

        "Feed review",

        5,

        5

    )

    assert learning.executions == 5



def test_preferred_action():

    service = DecisionLearningService()

    learning = service.analyze(

        "Feed review",

        10,

        8

    )

    assert service.preferred_action(learning)



def test_model():

    learning = DecisionLearningService().analyze(

        "Health review",

        4,

        2

    )

    assert learning.confidence == 50
'@ | Set-Content `
"tests\core\test_decision_learning.py"



Write-Host "HERD-047 Decision Learning Engine Build Complete"