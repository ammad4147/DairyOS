from dairyos.domain.events import Event


class DecisionEvents:
    """
    Creates domain events for operational decisions.

    Decision lifecycle:

        CREATED
            |
            v
        ACKNOWLEDGED
            |
            v
        COMPLETED
    """


    @staticmethod
    def created(
        decision,
    ) -> Event:

        return Event(

            name="OPERATIONAL_DECISION_CREATED",

            payload={

                "decision_id":
                    decision.decision_id,

                "title":
                    decision.title,

                "description":
                    decision.description,

                "priority":
                    decision.priority.level,

                "source":
                    decision.source,

                "owner_action_required":
                    decision.owner_action_required,

            },

        )


    @staticmethod
    def acknowledged(
        decision,
    ) -> Event:

        return Event(

            name="OPERATIONAL_DECISION_ACKNOWLEDGED",

            payload={

                "decision_id":
                    decision.decision_id,

                "owner":
                    decision.owner,

                "status":
                    decision.status,

                "source":
                    decision.source,

            },

        )


    @staticmethod
    def completed(
        decision,
    ) -> Event:

        return Event(

            name="OPERATIONAL_DECISION_COMPLETED",

            payload={

                "decision_id":
                    decision.decision_id,

                "outcome":
                    decision.outcome,

                "status":
                    decision.status,

                "source":
                    decision.source,

            },

        )