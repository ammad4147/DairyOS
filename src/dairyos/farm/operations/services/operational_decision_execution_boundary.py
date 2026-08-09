from dairyos.farm.operations.models.operational_decision_execution import (
    OperationalDecisionExecution,
)


class OperationalDecisionExecutionBoundary:
    """
    Controlled execution boundary between:

        Operational Decision
                 |
                 v
        Farm Operations Runtime


    Rules:

    - Decisions are never self executing.
    - Human approval required.
    - Runtime remains source of operational events.
    - Failed execution is recorded.
    """


    SUPPORTED_ACTIONS = {

        "record_milk_activity",

        "record_feed_activity",

        "record_workforce_activity",

        "record_inventory_activity",

        "record_equipment_activity",

        "record_financial_activity",

    }


    def __init__(
        self,
        farm_operations_runtime,
    ):

        self.runtime = (
            farm_operations_runtime
        )



    def execute(
        self,
        decision,
        approved_by,
    ):

        action = (
            decision.get("action")
            if isinstance(
                decision,
                dict,
            )
            else decision.action
        )


        decision_id = (
            decision.get("decision_id")
            if isinstance(
                decision,
                dict,
            )
            else decision.decision_id
        )


        execution = OperationalDecisionExecution(

            decision_id=decision_id,

            action=action,

            approved_by=approved_by,

        )


        if action not in self.SUPPORTED_ACTIONS:

            execution.reject(
                {
                    "reason":
                        "Unsupported execution action"
                }
            )

            return execution



        execution.approve()



        try:

            result = self._dispatch(
                action,
                decision,
            )


            execution.complete(
                result
            )


        except Exception as exc:

            execution.fail(
                {
                    "error":
                        str(exc)
                }
            )


        return execution



    def _dispatch(
        self,
        action,
        decision,
    ):

        details = (
            decision.get(
                "details",
                {},
            )
            if isinstance(
                decision,
                dict,
            )
            else decision.details
        )


        if action == "record_milk_activity":

            return self.runtime.record_milk(
                animal_id=details.get(
                    "animal_id"
                ),
                session=details.get(
                    "session",
                    "UNKNOWN",
                ),
                litres=details.get(
                    "litres",
                    0,
                ),
                operator="decision_execution",
            )


        if action == "record_feed_activity":

            return self.runtime.record_feed(
                animal_group=details.get(
                    "animal_group",
                    "UNKNOWN",
                ),
                feed_type=details.get(
                    "feed_type",
                    "UNKNOWN",
                ),
                quantity_kg=details.get(
                    "quantity_kg",
                    0,
                ),
                cost=details.get(
                    "cost",
                    0,
                ),
                operator="decision_execution",
            )


        if action == "record_workforce_activity":

            return self.runtime.record_workforce(
                metric_type=details.get(
                    "metric_type",
                    "UNKNOWN",
                ),
                value=details.get(
                    "value",
                    0,
                ),
                operator="decision_execution",
            )


        raise ValueError(
            f"Execution not implemented: {action}"
        )
