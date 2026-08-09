from dairyos.herd.dashboard.services.autonomous_monitoring_service import AutonomousMonitoringService



def test_event_detection():

    event = AutonomousMonitoringService().detect(

        "MON001",

        "PRODUCTION",

        12,

        10

    )

    assert event.event_id == "MON001"



def test_high_severity():

    event = AutonomousMonitoringService().detect(

        "MON002",

        "PRODUCTION",

        15,

        10

    )

    assert event.severity == "HIGH"



def test_normal_condition():

    event = AutonomousMonitoringService().detect(

        "MON003",

        "PRODUCTION",

        5,

        10

    )

    assert event.severity == "NORMAL"



def test_production_action():

    event = AutonomousMonitoringService().detect(

        "MON004",

        "PRODUCTION",

        20,

        10

    )

    assert event.recommended_action == "Review production factors"



def test_health_action():

    event = AutonomousMonitoringService().detect(

        "MON005",

        "HEALTH",

        20,

        10

    )

    assert event.recommended_action == "Review animal health status"



def test_reproduction_action():

    event = AutonomousMonitoringService().detect(

        "MON006",

        "REPRODUCTION",

        20,

        10

    )

    assert event.recommended_action == "Review breeding performance"



def test_finance_action():

    event = AutonomousMonitoringService().detect(

        "MON007",

        "FINANCE",

        20,

        10

    )

    assert event.recommended_action == "Review financial indicators"



def test_attention_required():

    service = AutonomousMonitoringService()

    event = service.detect(

        "MON008",

        "HEALTH",

        20,

        10

    )

    assert service.requires_attention(event)



def test_no_attention():

    service = AutonomousMonitoringService()

    event = service.detect(

        "MON009",

        "HEALTH",

        2,

        10

    )

    assert not service.requires_attention(event)



def test_model():

    event = AutonomousMonitoringService().detect(

        "MON010",

        "FINANCE",

        20,

        10

    )

    assert event.category == "FINANCE"
