from dairyos.intelligence.executive.services.executive_intelligence_service import ExecutiveIntelligenceService



def test_good_status():

    result = ExecutiveIntelligenceService().evaluate(

        "LOW",

        "GOOD",

        "POSITIVE",

        "POSITIVE"

    )

    assert result.overall_status == "GOOD"



def test_good_action():

    result = ExecutiveIntelligenceService().evaluate(

        "LOW",

        "GOOD",

        "POSITIVE",

        "POSITIVE"

    )

    assert result.priority_action == "Maintain current strategy"



def test_health_attention():

    result = ExecutiveIntelligenceService().evaluate(

        "HIGH",

        "GOOD",

        "POSITIVE",

        "POSITIVE"

    )

    assert result.overall_status == "ATTENTION"



def test_negative_finance():

    result = ExecutiveIntelligenceService().evaluate(

        "LOW",

        "GOOD",

        "POSITIVE",

        "NEGATIVE"

    )

    assert result.overall_status == "ATTENTION"



def test_monitor_status():

    result = ExecutiveIntelligenceService().evaluate(

        "MEDIUM",

        "GOOD",

        "POSITIVE",

        "POSITIVE"

    )

    assert result.overall_status == "MONITOR"



def test_monitor_action():

    result = ExecutiveIntelligenceService().evaluate(

        "MEDIUM",

        "GOOD",

        "POSITIVE",

        "POSITIVE"

    )

    assert result.priority_action == "Monitor identified risk areas"



def test_health_value():

    result = ExecutiveIntelligenceService().evaluate(

        "LOW",

        "GOOD",

        "POSITIVE",

        "POSITIVE"

    )

    assert result.health_status == "LOW"



def test_financial_value():

    result = ExecutiveIntelligenceService().evaluate(

        "LOW",

        "GOOD",

        "POSITIVE",

        "POSITIVE"

    )

    assert result.financial_status == "POSITIVE"



def test_production_value():

    result = ExecutiveIntelligenceService().evaluate(

        "LOW",

        "GOOD",

        "POSITIVE",

        "POSITIVE"

    )

    assert result.production_status == "POSITIVE"



def test_service_exists():

    assert ExecutiveIntelligenceService is not None
