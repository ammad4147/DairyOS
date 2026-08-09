$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-057 Adaptive Learning Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class AdaptiveLearning:


    strategy: str

    attempts: int

    successes: int

    success_rate: float

    confidence_adjustment: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\adaptive_learning.py"



@'
from ..models.adaptive_learning import AdaptiveLearning



class AdaptiveLearningService:



    def analyze(

        self,

        strategy,

        attempts,

        successes

    ):


        if attempts == 0:

            rate = 0

        else:

            rate = (successes / attempts) * 100



        if rate >= 80:

            adjustment = "INCREASE"

        elif rate >= 50:

            adjustment = "MAINTAIN"

        else:

            adjustment = "DECREASE"



        return AdaptiveLearning(

            strategy,

            attempts,

            successes,

            rate,

            adjustment

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\adaptive_learning_service.py"



@'
from dairyos.herd.dashboard.services.adaptive_learning_service import AdaptiveLearningService



def test_learning_creation():

    result = AdaptiveLearningService().analyze(

        "Feed Investigation",

        10,

        8

    )

    assert result.strategy == "Feed Investigation"



def test_attempts():

    result = AdaptiveLearningService().analyze(

        "Feed",

        10,

        8

    )

    assert result.attempts == 10



def test_successes():

    result = AdaptiveLearningService().analyze(

        "Feed",

        10,

        8

    )

    assert result.successes == 8



def test_success_rate():

    result = AdaptiveLearningService().analyze(

        "Feed",

        10,

        8

    )

    assert result.success_rate == 80



def test_increase_confidence():

    result = AdaptiveLearningService().analyze(

        "Feed",

        10,

        8

    )

    assert result.confidence_adjustment == "INCREASE"



def test_maintain_confidence():

    result = AdaptiveLearningService().analyze(

        "Feed",

        10,

        6

    )

    assert result.confidence_adjustment == "MAINTAIN"



def test_decrease_confidence():

    result = AdaptiveLearningService().analyze(

        "Feed",

        10,

        3

    )

    assert result.confidence_adjustment == "DECREASE"



def test_zero_attempts():

    result = AdaptiveLearningService().analyze(

        "Feed",

        0,

        0

    )

    assert result.success_rate == 0



def test_learning_type():

    result = AdaptiveLearningService().analyze(

        "Health",

        5,

        5

    )

    assert isinstance(result.success_rate, float)



def test_learning_flow():

    result = AdaptiveLearningService().analyze(

        "Feed Investigation",

        10,

        9

    )

    assert result.confidence_adjustment == "INCREASE"
'@ | Set-Content `
"tests\core\test_adaptive_learning.py"



Write-Host "HERD-057 Adaptive Learning Build Complete"