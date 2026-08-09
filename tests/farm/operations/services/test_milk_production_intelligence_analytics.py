from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.services.operational_state_query_service import (
    OperationalStateQueryService,
)



def test_milk_production_intelligence_analytics_projection():

    service = FarmOperationalStateService()


    service.process_event(

        FarmOperationEvent(

            event_type="milk_recorded",

            animal_id="MILKING-HERD",

            operator="Farm Manager",

            payload={

                "shift":
                    "Morning",

                "litres":
                    300,

                "status":
                    "completed",

            },

        )

    )


    query = OperationalStateQueryService(
        service
    )


    result = query.get_current_state()


    assert (
        result.milk_production_intelligence
    )


    assert (
        result.milk_production_intelligence["total_litres"]
        ==
        300
    )



def test_milk_production_intelligence_tracks_shift_output():

    service = FarmOperationalStateService()


    service.process_event(

        FarmOperationEvent(

            event_type="milk_recorded",

            animal_id="MILKING-HERD",

            operator="Farm Manager",

            payload={

                "shift":
                    "Evening",

                "litres":
                    250,

                "status":
                    "completed",

            },

        )

    )


    query = OperationalStateQueryService(
        service
    )


    result = query.get_current_state()


    intelligence = (
        result.milk_production_intelligence
    )


    assert (
        intelligence["shift_production"]["Evening"]
        ==
        250
    )
