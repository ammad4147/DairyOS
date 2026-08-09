from dairyos.herd.dashboard.services.escalation_service import EscalationService



def test_owner_attention_escalation():

    result = EscalationService().evaluate(

        95,

        "HERD STRATEGY"

    )

    assert result.level == "OWNER ATTENTION"



def test_manager_attention_escalation():

    result = EscalationService().evaluate(

        70,

        "HEALTH"

    )

    assert result.level == "MANAGER ATTENTION"



def test_monitor_level():

    result = EscalationService().evaluate(

        30,

        "PRODUCTION"

    )

    assert result.level == "MONITOR"



def test_owner_identification():

    result = EscalationService().evaluate(

        95

    )

    assert result.response_owner == "OWNER"



def test_manager_identification():

    result = EscalationService().evaluate(

        70

    )

    assert result.response_owner == "FARM MANAGER"



def test_response_time():

    result = EscalationService().evaluate(

        95

    )

    assert result.response_time == "7 DAYS"



def test_reason_generation():

    result = EscalationService().evaluate(

        90,

        "REPRODUCTION"

    )

    assert "REPRODUCTION" in result.reason



def test_owner_attention_check():

    result = EscalationService().evaluate(

        95

    )

    assert EscalationService().requires_owner_attention(result)



def test_sorting():

    service = EscalationService()

    results = service.sort_escalations([

        service.evaluate(30),

        service.evaluate(95)

    ])

    assert results[0].priority_score == 95



def test_model_creation():

    result = EscalationService().evaluate(

        60

    )

    assert result.priority_score == 60
