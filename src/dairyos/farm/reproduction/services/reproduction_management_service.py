from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)


class ReproductionManagementService:
    """
    Handles reproductive operations.

    Responsibilities:

    - record insemination
    - record pregnancy confirmation
    - optionally publish operational events

    Persistence remains owned by repository.
    Event publication is optional infrastructure.
    """



    def __init__(
        self,
        repository,
        event_bus=None,
    ):

        self.repository = repository

        self.event_bus = event_bus



    def _publish_event(
        self,
        event_type,
        animal_id,
        payload,
        operator,
    ):
        """
        Publishes reproduction operational event
        when event infrastructure is available.
        """

        if self.event_bus is None:

            return


        self.event_bus.publish(

            FarmOperationEvent(

                event_type=event_type,

                animal_id=animal_id,

                operator=operator,

                payload=payload,

            )

        )



    def record_insemination(
        self,
        record,
    ):

        saved = self.repository.save_insemination(
            record
        )


        self._publish_event(

            event_type="insemination_recorded",

            animal_id=record.animal_id,

            payload={

                "insemination_id":
                    record.insemination_id,

                "semen_type":
                    record.semen_type,

                "bull_reference":
                    record.bull_reference,

                "technician":
                    record.technician,

            },

            operator=record.technician,

        )


        return saved



    def record_pregnancy(
        self,
        record,
    ):

        saved = self.repository.save_pregnancy(
            record
        )


        self._publish_event(

            event_type="pregnancy_confirmed",

            animal_id=record.animal_id,

            payload={

                "pregnancy_id":
                    record.pregnancy_id,

                "confirmed":
                    record.confirmed,

                "expected_calving_date":
                    record.expected_calving_date,

                "checked_by":
                    record.checked_by,

            },

            operator=record.checked_by,

        )


        return saved



    def pregnant_animals(
        self,
    ):

        return [

            item

            for item

            in self.repository.get_pregnancies()

            if item.confirmed

        ]
