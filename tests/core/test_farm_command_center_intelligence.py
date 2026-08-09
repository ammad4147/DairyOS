from dairyos.herd.dashboard.services.command_center_intelligence_service import CommandCenterIntelligenceService



def test_health_index_calculation():

    result = CommandCenterIntelligenceService().calculate_health_index(

        100,

        100,

        100,

        100

    )

    assert result.overall_score == 100



def test_health_index_weighting():

    result = CommandCenterIntelligenceService().calculate_health_index(

        50,

        100,

        100,

        100

    )

    assert result.overall_score == 80



def test_green_status():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(100,100,100,100)

    status = service.evaluate_status(index,"LOW")

    assert status.status == "GREEN"



def test_yellow_status():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(80,80,80,80)

    status = service.evaluate_status(index,"MEDIUM")

    assert status.status == "YELLOW"



def test_red_status():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(50,50,50,50)

    status = service.evaluate_status(index,"HIGH")

    assert status.status == "RED"



def test_status_priority():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(50,50,50,50)

    status = service.evaluate_status(index,"HIGH")

    assert status.priority == "HIGH"



def test_status_reason():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(100,100,100,100)

    status = service.evaluate_status(index,"LOW")

    assert len(status.reason) > 0



def test_index_model():

    result = CommandCenterIntelligenceService().calculate_health_index(

        90,90,90,90

    )

    assert result.production_score == 90



def test_medium_risk():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(100,100,100,100)

    status = service.evaluate_status(index,"MEDIUM")

    assert status.status == "YELLOW"
