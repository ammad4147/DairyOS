from dairyos.herd.health.services.health_event_service import (
    HealthEventService
)



def test_create_health_event():


    result = HealthEventService().create_event(

        "HF-2001",

        "MILK_DROP",

        "Milk production reduced by 30 percent",

        "HIGH",

        "Milking Operator"

    )


    assert result.animal_id == "HF-2001"



def test_event_status_open():


    result = HealthEventService().create_event(

        "HF-2002",

        "APPETITE_CHANGE",

        "Reduced feed intake",

        "MEDIUM",

        "Farm Manager"

    )


    assert result.status == "OPEN"



def test_event_reporter():


    result = HealthEventService().create_event(

        "HF-2003",

        "TEMPERATURE",

        "High temperature detected",

        "HIGH",

        "Veterinarian"

    )


    assert result.reported_by == "Veterinarian"



def test_get_animal_events():


    service = HealthEventService()


    service.create_event(

        "HF-2004",

        "GENERAL",

        "Observation",

        "LOW",

        "Worker"

    )


    result = service.get_animal_events(

        "HF-2004"

    )


    assert len(result) == 1



def test_close_event():


    service = HealthEventService()


    event = service.create_event(

        "HF-2005",

        "INJURY",

        "Leg injury",

        "HIGH",

        "Manager"

    )


    service.close_event(event)


    assert event.status == "CLOSED"
