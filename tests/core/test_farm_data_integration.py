from dairyos.data.integration.services.farm_data_integration_service import FarmDataIntegrationService



def test_event_id():

    event = FarmDataIntegrationService().create_event(

        "EV001",

        "MILK_PRODUCTION",

        "Production",

        "COW001",

        25

    )

    assert event.event_id == "EV001"



def test_event_type():

    event = FarmDataIntegrationService().create_event(

        "EV001",

        "MILK_PRODUCTION",

        "Production",

        "COW001",

        25

    )

    assert event.event_type == "MILK_PRODUCTION"



def test_source_module():

    event = FarmDataIntegrationService().create_event(

        "EV001",

        "MILK_PRODUCTION",

        "Production",

        "COW001",

        25

    )

    assert event.source_module == "Production"



def test_entity():

    event = FarmDataIntegrationService().create_event(

        "EV001",

        "MILK_PRODUCTION",

        "Production",

        "COW001",

        25

    )

    assert event.entity_id == "COW001"



def test_value():

    event = FarmDataIntegrationService().create_event(

        "EV001",

        "MILK_PRODUCTION",

        "Production",

        "COW001",

        25

    )

    assert event.value == 25



def test_status():

    event = FarmDataIntegrationService().create_event(

        "EV001",

        "MILK_PRODUCTION",

        "Production",

        "COW001",

        25

    )

    assert event.status == "SYNCED"



def test_health_event():

    event = FarmDataIntegrationService().create_event(

        "EV002",

        "HEALTH_CHECK",

        "Health",

        "COW002",

        1

    )

    assert event.event_type == "HEALTH_CHECK"



def test_feed_event():

    event = FarmDataIntegrationService().create_event(

        "EV003",

        "FEED_USAGE",

        "Feed",

        "COW003",

        20

    )

    assert event.source_module == "Feed"



def test_finance_event():

    event = FarmDataIntegrationService().create_event(

        "EV004",

        "EXPENSE",

        "Finance",

        "FARM001",

        50000

    )

    assert event.status == "SYNCED"



def test_integration_service():

    assert FarmDataIntegrationService is not None
