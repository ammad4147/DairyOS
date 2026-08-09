from dairyos.herd.dashboard.services.herd_command_service import HerdCommandService



def test_command_creation():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100

    )


    assert result.farm_name == "Trident Dairies"

    assert result.total_animals == 100



def test_stable_herd_status():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100

    )


    assert result.overall_risk == "LOW"



def test_health_warning():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100,

        health_alerts=2

    )


    assert result.health_status == "ATTENTION REQUIRED"

    assert result.overall_risk == "MEDIUM"



def test_reproduction_warning():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100,

        open_cows=5

    )


    assert result.reproduction_status == "MONITOR"



def test_replacement_shortage():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100,

        replacement_shortage=True

    )


    assert result.overall_risk == "HIGH"



def test_owner_attention():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100,

        health_alerts=1

    )


    assert "health" in result.owner_attention.lower()
