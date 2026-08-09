from dairyos.herd.intelligence.services.decision_service import DecisionService
from dairyos.herd.events.services.event_intelligence_bridge import EventIntelligenceBridge


def test_low_risk_decision():

    service = DecisionService()

    result = service.evaluate()

    assert result.risk_level == "LOW"

    assert result.attention_required is False



def test_health_alert_decision():

    service = DecisionService()

    result = service.evaluate(
        health_alerts=2
    )

    assert result.attention_required is True

    assert "Review animal health alerts" in result.recommendations



def test_reproduction_warning():

    service = DecisionService()

    result = service.evaluate(
        open_cows=5
    )

    assert result.risk_level == "MEDIUM"



def test_replacement_shortage():

    service = DecisionService()

    result = service.evaluate(
        replacement_shortage=True
    )

    assert result.risk_level == "HIGH"



def test_event_birth_bridge():

    bridge = EventIntelligenceBridge()

    result = bridge.analyze(
        "BIRTH"
    )

    assert "New calf registered" in result



def test_event_calving_bridge():

    bridge = EventIntelligenceBridge()

    result = bridge.analyze(
        "CALVING"
    )

    assert "Lactation cycle started" in result
