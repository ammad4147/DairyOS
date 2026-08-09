from dairyos.herd.dashboard.services.decision_assistant_service import DecisionAssistantService



def test_assistant_creation():

    result = DecisionAssistantService().advise(

        "Production decline detected",

        "Review feed quality",

        85

    )

    assert result.situation == "Production decline detected"



def test_recommendation():

    result = DecisionAssistantService().advise(

        "Health risk detected",

        "Review health indicators",

        80

    )

    assert result.recommended_action == "Review health indicators"



def test_high_priority():

    result = DecisionAssistantService().advise(

        "Risk detected",

        "Action",

        85

    )

    assert result.priority == "HIGH"



def test_medium_priority():

    result = DecisionAssistantService().advise(

        "Risk detected",

        "Action",

        60

    )

    assert result.priority == "MEDIUM"



def test_low_priority():

    result = DecisionAssistantService().advise(

        "Risk detected",

        "Action",

        30

    )

    assert result.priority == "LOW"



def test_confidence():

    result = DecisionAssistantService().advise(

        "Risk",

        "Action",

        85

    )

    assert result.confidence == 85



def test_reason():

    result = DecisionAssistantService().advise(

        "Risk",

        "Action",

        85

    )

    assert "confidence" in result.reason



def test_finance_case():

    result = DecisionAssistantService().advise(

        "Financial risk",

        "Review costs",

        70

    )

    assert result.recommended_action == "Review costs"



def test_production_case():

    result = DecisionAssistantService().advise(

        "Production risk",

        "Review feed",

        90

    )

    assert result.priority == "HIGH"



def test_model():

    result = DecisionAssistantService().advise(

        "Situation",

        "Action",

        50

    )

    assert result.confidence == 50
