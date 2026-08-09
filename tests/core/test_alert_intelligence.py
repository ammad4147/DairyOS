from dairyos.herd.dashboard.services.alert_intelligence_service import AlertIntelligenceService



def test_high_alert_creation():

    alert = AlertIntelligenceService().generate_alert(

        "HEALTH",

        "Disease warning",

        "HIGH"

    )

    assert alert.severity == "HIGH"



def test_high_alert_urgency():

    alert = AlertIntelligenceService().generate_alert(

        "REPRODUCTION",

        "Open cows",

        "HIGH"

    )

    assert alert.urgency == "IMMEDIATE"



def test_low_alert():

    alert = AlertIntelligenceService().generate_alert(

        "PRODUCTION",

        "Monitor output"

    )

    assert alert.priority_score == 30



def test_health_action():

    alert = AlertIntelligenceService().generate_alert(

        "HEALTH",

        "Issue"

    )

    assert alert.recommended_action == "Review animal health alerts"



def test_reproduction_action():

    alert = AlertIntelligenceService().generate_alert(

        "REPRODUCTION",

        "Issue"

    )

    assert alert.recommended_action == "Review breeding performance"



def test_alert_ranking():

    service = AlertIntelligenceService()

    alerts = [

        service.generate_alert(

            "HEALTH",

            "Issue",

            "LOW"

        ),

        service.generate_alert(

            "HERD STRATEGY",

            "Issue",

            "HIGH"

        )

    ]


    ranked = service.rank_alerts(alerts)


    assert ranked[0].severity == "HIGH"



def test_highest_priority():

    service = AlertIntelligenceService()

    alerts = [

        service.generate_alert(

            "FINANCE",

            "Issue",

            "MEDIUM"

        ),

        service.generate_alert(

            "HEALTH",

            "Issue",

            "HIGH"

        )

    ]


    assert service.highest_priority(alerts).category == "HEALTH"



def test_empty_alerts():

    assert AlertIntelligenceService().highest_priority([]) is None



def test_score_generation():

    alert = AlertIntelligenceService().generate_alert(

        "FINANCE",

        "Cash warning",

        "MEDIUM"

    )

    assert alert.priority_score == 60



def test_alert_model():

    alert = AlertIntelligenceService().generate_alert(

        "HERD STRATEGY",

        "Replacement shortage",

        "HIGH"

    )

    assert alert.category == "HERD STRATEGY"
