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
