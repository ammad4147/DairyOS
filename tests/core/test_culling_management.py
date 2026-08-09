from dairyos.herd.culling.services.culling_management_service import CullingManagementService



def test_animal_id():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.animal_id == "HF-1040"



def test_production_status():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.production_status == "Below Target"



def test_health_status():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.health_status == "Repeated Issues"



def test_replacement_status():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.replacement_available is True



def test_culling_recommendation():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.recommendation == "CONSIDER CULLING"



def test_culling_action():

    result = CullingManagementService().evaluate(

        "HF-1040",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.action == "Veterinary and economic assessment"



def test_health_review():

    result = CullingManagementService().evaluate(

        "HF-1041",

        "Normal",

        "Repeated Issues",

        False

    )

    assert result.recommendation == "REVIEW"



def test_retain_animal():

    result = CullingManagementService().evaluate(

        "HF-1042",

        "On Target",

        "Healthy",

        False

    )

    assert result.recommendation == "RETAIN"



def test_action_exists():

    result = CullingManagementService().evaluate(

        "HF-1043",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert len(result.action) > 0



def test_culling_flow():

    result = CullingManagementService().evaluate(

        "HF-1044",

        "Below Target",

        "Repeated Issues",

        True

    )

    assert result.recommendation == "CONSIDER CULLING"
