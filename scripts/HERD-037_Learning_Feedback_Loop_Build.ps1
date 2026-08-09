$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-037 Learning Feedback Loop Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class LearningSignal:


    category: str

    decision: str

    outcome: str

    effectiveness: str

    confidence_adjustment: int

    learning_note: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\learning_signal.py"



@'
from ..models.learning_signal import LearningSignal



class LearningFeedbackService:



    def evaluate(

        self,

        category,

        decision,

        outcome,

        success=True

    ):


        if success:

            effectiveness = "HIGH"

            adjustment = 15

            note = "Successful decision should improve future confidence"


        else:

            effectiveness = "LOW"

            adjustment = -10

            note = "Decision requires review before repeating"



        return LearningSignal(

            category,

            decision,

            outcome,

            effectiveness,

            adjustment,

            note

        )



    def confidence_score(

        self,

        signals

    ):


        if not signals:

            return 0


        return sum(

            signal.confidence_adjustment

            for signal in signals

        )



    def successful_actions(

        self,

        signals

    ):


        return [

            signal

            for signal in signals

            if signal.effectiveness == "HIGH"

        ]
'@ | Set-Content `
"dairyos\herd\dashboard\services\learning_feedback_service.py"



@'
from dairyos.herd.dashboard.services.learning_feedback_service import LearningFeedbackService



def test_learning_signal_creation():

    signal = LearningFeedbackService().evaluate(

        "HERD STRATEGY",

        "Purchase replacements",

        "Herd stabilized"

    )

    assert signal.category == "HERD STRATEGY"



def test_success_effectiveness():

    signal = LearningFeedbackService().evaluate(

        "HEALTH",

        "Vaccination",

        "Disease reduced"

    )

    assert signal.effectiveness == "HIGH"



def test_failed_effectiveness():

    signal = LearningFeedbackService().evaluate(

        "PRODUCTION",

        "Feed change",

        "No improvement",

        False

    )

    assert signal.effectiveness == "LOW"



def test_positive_learning():

    signal = LearningFeedbackService().evaluate(

        "REPRODUCTION",

        "Breeding review",

        "Conception improved"

    )

    assert signal.confidence_adjustment == 15



def test_negative_learning():

    signal = LearningFeedbackService().evaluate(

        "FINANCE",

        "Cost reduction",

        "Target missed",

        False

    )

    assert signal.confidence_adjustment == -10



def test_learning_note():

    signal = LearningFeedbackService().evaluate(

        "HEALTH",

        "Treatment",

        "Recovered"

    )

    assert "Successful" in signal.learning_note



def test_confidence_score():

    service = LearningFeedbackService()

    signals = [

        service.evaluate(

            "A",

            "B",

            "C"

        ),

        service.evaluate(

            "D",

            "E",

            "F"

        )

    ]

    assert service.confidence_score(signals) == 30



def test_empty_confidence():

    assert LearningFeedbackService().confidence_score([]) == 0



def test_successful_actions():

    service = LearningFeedbackService()

    signals = [

        service.evaluate(

            "HEALTH",

            "A",

            "B"

        )

    ]

    assert len(service.successful_actions(signals)) == 1



def test_learning_model():

    signal = LearningFeedbackService().evaluate(

        "HERD",

        "Decision",

        "Outcome"

    )

    assert signal.decision == "Decision"
'@ | Set-Content `
"tests\core\test_learning_feedback.py"



Write-Host "HERD-037 Learning Feedback Loop Build Complete"