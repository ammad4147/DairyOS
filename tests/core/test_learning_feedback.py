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
