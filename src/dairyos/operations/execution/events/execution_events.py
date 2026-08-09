from dairyos.domain.events import Event


class ExecutionEvents:
    """
    Creates domain events for operational execution lifecycle.
    """


    @staticmethod
    def created(
        execution,
    ) -> Event:

        return Event(

            name="OPERATIONAL_EXECUTION_CREATED",

            payload={

                "execution_id":
                    execution.execution_id,

                "action_id":
                    execution.action_id,

                "assigned_to":
                    execution.assigned_to,

                "status":
                    execution.status,

            },

        )


    @staticmethod
    def assigned(
        execution,
    ) -> Event:

        return Event(

            name="OPERATIONAL_EXECUTION_ASSIGNED",

            payload={

                "execution_id":
                    execution.execution_id,

                "assigned_to":
                    execution.assigned_to,

            },

        )


    @staticmethod
    def acknowledged(
        execution,
    ) -> Event:

        return Event(

            name="OPERATIONAL_EXECUTION_ACKNOWLEDGED",

            payload={

                "execution_id":
                    execution.execution_id,

                "acknowledged_by":
                    execution.acknowledged_by,

            },

        )


    @staticmethod
    def started(
        execution,
    ) -> Event:

        return Event(

            name="OPERATIONAL_EXECUTION_STARTED",

            payload={

                "execution_id":
                    execution.execution_id,

                "started_by":
                    execution.started_by,

            },

        )


    @staticmethod
    def completed(
        execution,
    ) -> Event:

        return Event(

            name="OPERATIONAL_EXECUTION_COMPLETED",

            payload={

                "execution_id":
                    execution.execution_id,

                "completed_by":
                    execution.completed_by,

                "notes":
                    execution.notes,

            },

        )


    @staticmethod
    def verified(
        execution,
    ) -> Event:

        return Event(

            name="OPERATIONAL_EXECUTION_VERIFIED",

            payload={

                "execution_id":
                    execution.execution_id,

                "verified_by":
                    execution.verified_by,

            },

        )


    @staticmethod
    def closed(
        execution,
    ) -> Event:

        return Event(

            name="OPERATIONAL_EXECUTION_CLOSED",

            payload={

                "execution_id":
                    execution.execution_id,

            },

        )
