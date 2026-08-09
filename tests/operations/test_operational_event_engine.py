from dairyos.operations.events.operational_event import (
    OperationalEvent,
)


from dairyos.operations.services.event_service import (
    EventService,
)



def test_operational_event_creation():


    event = OperationalEvent(

        event_type="milking",

        farm_id="trident",

        entity_id="cow102",

        performed_by="worker01",

    )



    assert event.event_type == "milking"


    assert event.entity_id == "cow102"


    assert event.status == "recorded"




def test_event_service_storage():


    service = EventService()



    event = OperationalEvent(

        event_type="feeding",

        farm_id="trident",

        performed_by="worker01",

    )



    service.record(event)



    assert len(

        service.all_events()

    ) == 1

