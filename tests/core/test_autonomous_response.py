from dairyos.herd.dashboard.services.autonomous_response_service import AutonomousResponseService



def test_response_creation():

    response = AutonomousResponseService().generate_response(

        "Milk yield decline"

    )

    assert response.condition == "Milk yield decline"



def test_primary_response():

    response = AutonomousResponseService().generate_response(

        "Milk production decline"

    )

    assert response.primary_response == "Feed Investigation"



def test_confidence():

    response = AutonomousResponseService().generate_response(

        "Milk yield decline"

    )

    assert response.confidence == 85



def test_supporting_actions():

    response = AutonomousResponseService().generate_response(

        "Milk yield decline"

    )

    assert len(response.supporting_actions) == 3



def test_ration_action():

    response = AutonomousResponseService().generate_response(

        "Production decline"

    )

    assert "Review ration" in response.supporting_actions



def test_health_action():

    response = AutonomousResponseService().generate_response(

        "Production decline"

    )

    assert "Check health" in response.supporting_actions



def test_environment_action():

    response = AutonomousResponseService().generate_response(

        "Production decline"

    )

    assert "Verify environment" in response.supporting_actions



def test_general_response():

    response = AutonomousResponseService().generate_response(

        "Routine observation"

    )

    assert response.primary_response == "General Review"



def test_general_confidence():

    response = AutonomousResponseService().generate_response(

        "Routine observation"

    )

    assert response.confidence == 50



def test_model():

    response = AutonomousResponseService().generate_response(

        "Condition"

    )

    assert isinstance(response.supporting_actions, list)
