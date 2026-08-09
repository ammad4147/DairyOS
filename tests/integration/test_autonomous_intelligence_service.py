from dairyos.intelligence.application.autonomous_intelligence_service import (
    AutonomousIntelligenceService,
)


def test_autonomous_intelligence_service_creation():

    service = AutonomousIntelligenceService()

    assert service is not None



def test_autonomous_intelligence_service_status():

    service = AutonomousIntelligenceService()

    status = service.get_runtime_status()

    assert (
        status["status"]
        == "operational"
    )
