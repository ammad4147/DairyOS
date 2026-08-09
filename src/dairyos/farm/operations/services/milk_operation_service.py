from dairyos.farm.operations.models.milk_record import (
    MilkRecord,
)

from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


class MilkOperationService:
    """
    Processes daily milk production entries.
    """


    def record(
        self,
        record: MilkRecord,
    ):

        return FarmOperationEvent(

            event_type="milk_recorded",

            animal_id=(
                record.animal_id
                if record.animal_id
                else record.animal_group
            ),

            operator=record.operator,

            payload={
                "litres": record.litres,
                "shift": record.shift,
            },
        )
