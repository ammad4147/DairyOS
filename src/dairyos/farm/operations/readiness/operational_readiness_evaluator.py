class OperationalReadinessEvaluator:
    """
    Evaluates whether the farm operational state
    is ready for execution.

    This layer does not create data.
    It only interprets FarmOperationalState.

    Farm Operational State remains the source of truth.
    """


    def __init__(
        self,
        operational_state_service,
    ):

        self.operational_state_service = (
            operational_state_service
        )


    def evaluate(
        self,
    ):

        state = (
            self.operational_state_service
            .get_state()
        )


        areas = {

            "milk": self._evaluate_milk(
                state
            ),

            "feeding": self._evaluate_feeding(
                state
            ),

            "health": self._evaluate_health(
                state
            ),

            "breeding": self._evaluate_breeding(
                state
            ),

            "inventory": self._evaluate_inventory(
                state
            ),

            "equipment": self._evaluate_equipment(
                state
            ),

            "workforce": self._evaluate_workforce(
                state
            ),

        }


        risks = []


        for name, area in areas.items():

            if area["status"] != "READY":

                risks.append(
                    {
                        "area": name,
                        "status": area["status"],
                        "reason": area["reason"],
                    }
                )


        return {

            "overall_status":
                self._overall_status(
                    risks
                ),

            "areas":
                areas,

            "risks":
                risks,

        }



    def _overall_status(
        self,
        risks,
    ):

        if any(
            r["status"] == "CRITICAL"
            for r in risks
        ):

            return "CRITICAL"


        if risks:

            return "ATTENTION_REQUIRED"


        return "READY"



    def _evaluate_milk(
        self,
        state,
    ):

        if not state.milk_status:

            return {
                "status": "ATTENTION_REQUIRED",
                "reason": "No milk activity recorded",
            }


        return {
            "status": "READY",
            "reason": "Milk activity available",
        }



    def _evaluate_feeding(
        self,
        state,
    ):

        if not state.feeding_status:

            return {
                "status": "ATTENTION_REQUIRED",
                "reason": "No feeding activity recorded",
            }


        return {
            "status": "READY",
            "reason": "Feeding activity available",
        }



    def _evaluate_health(
        self,
        state,
    ):

        if state.health_status() == "critical":

            return {
                "status": "CRITICAL",
                "reason": "Critical health alerts present",
            }


        return {
            "status": "READY",
            "reason": "No critical health issues",
        }



    def _evaluate_breeding(
        self,
        state,
    ):

        return {
            "status": "READY",
            "reason": "Breeding state available",
        }



    def _evaluate_inventory(
        self,
        state,
    ):

        for inventory in state.inventory_status.values():

            if inventory.get(
                "status"
            ) == "CRITICAL":

                return {
                    "status": "CRITICAL",
                    "reason": "Critical inventory condition",
                }


        return {
            "status": "READY",
            "reason": "Inventory within monitored state",
        }



    def _evaluate_equipment(
        self,
        state,
    ):

        for equipment in state.equipment_status.values():

            if equipment.get(
                "operational_status"
            ) == "ATTENTION":

                return {
                    "status": "ATTENTION_REQUIRED",
                    "reason": "Equipment requires attention",
                }


        return {
            "status": "READY",
            "reason": "Equipment available",
        }



    def _evaluate_workforce(
        self,
        state,
    ):

        for value in state.workforce_status.values():

            if isinstance(
                value,
                int,
            ) and value > 0:

                return {
                    "status": "ATTENTION_REQUIRED",
                    "reason": "Pending workforce workload",
                }


        return {
            "status": "READY",
            "reason": "Workforce state available",
        }
