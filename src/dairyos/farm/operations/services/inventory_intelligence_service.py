from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class InventoryIntelligenceService:
    """
    Operational intelligence for farm inventory execution.

    Converts inventory operational state into
    actionable attention items.

    Rules:
    - Reads FarmOperationalState only.
    - Does not modify operational facts.
    - Does not manage purchasing.
    - Does not replace inventory transactions.

    Inventory truth remains inside:
        FarmOperationalState.inventory_status
    """



    def evaluate(
        self,
        state: FarmOperationalState,
    ) -> list[dict]:
        """
        Evaluate inventory operational condition.

        Returns operational attention items.
        """

        decisions = []


        inventory_status = (
            state.inventory_status
            if state.inventory_status
            else {}
        )


        self._check_inventory_status(
            inventory_status,
            decisions,
        )


        self._check_inventory_visibility(
            inventory_status,
            decisions,
        )


        return decisions



    def _check_inventory_status(
        self,
        inventory_status,
        decisions,
    ):
        """
        Detect inventory risk conditions.
        """

        for inventory_type, inventory in (
            inventory_status.items()
        ):

            status = inventory.get(
                "status",
                "",
            )


            if (
                isinstance(
                    status,
                    str,
                )
                and
                status.upper()
                == "CRITICAL"
            ):

                decisions.append(
                    {
                        "type":
                            "inventory",

                        "priority":
                            "HIGH",

                        "action":
                            "review_inventory_shortage",

                        "title":
                            f"Review {inventory_type} inventory shortage",

                        "details":
                            {
                                "inventory_type":
                                    inventory_type,

                                "inventory":
                                    inventory,
                            },
                    }
                )



            elif (
                isinstance(
                    status,
                    str,
                )
                and
                status.upper()
                == "MONITOR"
            ):

                decisions.append(
                    {
                        "type":
                            "inventory",

                        "priority":
                            "NORMAL",

                        "action":
                            "monitor_inventory_status",

                        "title":
                            f"Monitor {inventory_type} inventory",

                        "details":
                            {
                                "inventory_type":
                                    inventory_type,

                                "inventory":
                                    inventory,
                            },
                    }
                )



    def _check_inventory_visibility(
        self,
        inventory_status,
        decisions,
    ):
        """
        Detect missing inventory operational visibility.
        """

        if not inventory_status:

            decisions.append(
                {
                    "type":
                        "inventory",

                    "priority":
                        "WARNING",

                    "action":
                        "record_inventory_activity",

                    "title":
                        "Inventory operational data unavailable",

                    "details":
                        {},
                }
            )
