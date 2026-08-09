from dairyos.platform.digital_twin.synchronization.services.digital_twin_sync_service import (
    DigitalTwinSyncService,
)



def test_digital_twin_synchronization():


    service = DigitalTwinSyncService()



    event = service.synchronize(

        source="herd_operations",

        event_type="milk_update",

        entity_id="farm_001",

        payload={

            "milk":625

        },

    )



    assert event.source == "herd_operations"


    assert len(service.history()) == 1

