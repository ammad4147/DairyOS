from dairyos.farm.command_center.assemblers.operational_command_center_assembler import (
    OperationalCommandCenterAssembler,
)

from dairyos.farm.command_center.services.attention_queue_service import (
    AttentionQueueService,
)


class OperationalCommandCenterService:
    """
    Aggregates the current operational picture of the farm.

    This service owns no business rules.
    It simply composes outputs from existing services.
    """

    def __init__(
        self,
        *,
        operational_state_service,
        operations_health_service,
        assembler=None,
        attention_queue_service=None,
    ):

        self.operational_state_service = (
            operational_state_service
        )

        self.operations_health_service = (
            operations_health_service
        )

        self.attention_queue_service = (
            attention_queue_service
            or AttentionQueueService()
        )

        self.assembler = (
            assembler
            or OperationalCommandCenterAssembler()
        )


    def snapshot(self):

        farm_state_object = (
            self.operational_state_service.get_state()
        )

        farm_state = farm_state_object.summary()


        health = (
            self.operations_health_service.generate_snapshot()
        )


        attention_queue = (
            self.attention_queue_service.build(
                farm_state=farm_state_object
            )
        )


        farm_state["attention_queue"] = [

            item.__dict__

            for item in attention_queue

        ]


        return self.assembler.assemble(

            farm_state=farm_state,

            health={

                "health_status":
                    health.health_status,

                "operational_score":
                    health.operational_score,

                "active_decisions":
                    health.active_decisions,

                "pending_actions":
                    health.pending_actions,

                "tracked_outcomes":
                    health.tracked_outcomes,

                "learning_signals":
                    health.learning_signals,

                "owner_attention_required":
                    health.owner_attention_required,

            },

            dashboard={},

            notifications=[],

            decisions={},

            execution={},

            intelligence={},

        )


    def get_snapshot(self):

        return self.snapshot()
