from dairyos.herd.dashboard.services.intelligence_orchestration_service import IntelligenceOrchestrationService



def test_orchestration_creation():

    result = IntelligenceOrchestrationService().coordinate(

        "Production risk",

        "Review feed quality",

        85

    )

    assert result.primary_issue == "Production risk"



def test_action():

    result = IntelligenceOrchestrationService().coordinate(

        "Health risk",

        "Review health indicators",

        80

    )

    assert result.recommended_action == "Review health indicators"



def test_high_attention():

    result = IntelligenceOrchestrationService().coordinate(

        "Risk",

        "Action",

        85

    )

    assert result.overall_status == "ATTENTION REQUIRED"



def test_medium_monitor():

    result = IntelligenceOrchestrationService().coordinate(

        "Risk",

        "Action",

        60

    )

    assert result.overall_status == "MONITOR"



def test_low_stable():

    result = IntelligenceOrchestrationService().coordinate(

        "Risk",

        "Action",

        20

    )

    assert result.overall_status == "STABLE"



def test_high_priority():

    result = IntelligenceOrchestrationService().coordinate(

        "Risk",

        "Action",

        90

    )

    assert result.priority == "HIGH"



def test_medium_priority():

    result = IntelligenceOrchestrationService().coordinate(

        "Risk",

        "Action",

        60

    )

    assert result.priority == "MEDIUM"



def test_low_priority():

    result = IntelligenceOrchestrationService().coordinate(

        "Risk",

        "Action",

        20

    )

    assert result.priority == "LOW"



def test_confidence():

    result = IntelligenceOrchestrationService().coordinate(

        "Risk",

        "Action",

        85

    )

    assert result.confidence == 85



def test_model_fields():

    result = IntelligenceOrchestrationService().coordinate(

        "Issue",

        "Action",

        70

    )

    assert result.recommended_action == "Action"
