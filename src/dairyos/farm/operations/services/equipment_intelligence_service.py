from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class EquipmentIntelligenceService:
    """
    Operational intelligence for farm equipment execution.

    Converts equipment operational state into
    actionable attention items.

    Rules:
    - Reads FarmOperationalState only.
    - Does not modify operational facts.
    - Does not perform maintenance.
    - Does not replace equipment management.

    Equipment truth remains inside:
        FarmOperationalState.equipment_status
    """



    def evaluate(
        self,
        state: FarmOperationalState,
    ) -> list[dict]:
        """
        Evaluate equipment operational condition.

        Returns operational attention items.
        """

        decisions = []


        equipment_status = (
            state.equipment_status
            if state.equipment_status
            else {}
        )


        self._check_equipment_status(
            equipment_status,
            decisions,
        )


        self._check_equipment_visibility(
            equipment_status,
            decisions,
        )


        return decisions



    def _check_equipment_status(
        self,
        equipment_status,
        decisions,
    ):
        """
        Detect equipment attention conditions.

        Watches for the governed `equipment_states` vocabulary
        (dairyos.api.reference_data.GOVERNED["equipment_states"] ==
        AVAILABLE/IN_USE/MAINTENANCE/OUT_OF_SERVICE), not an invented
        ATTENTION/FAILED/CRITICAL vocabulary the operator UI's governed
        dropdown can never produce (G9.1, decided 2026-08-13: keep the
        governed vocabulary, fix the check -- not the other way round).
        A later pass can add a MAINTENANCE-past-due check once
        `next_service_due_at` (G9.3) exists; there is no such field yet,
        so MAINTENANCE alone is not itself an attention condition.
        """

        for equipment_id, equipment in (
            equipment_status.items()
        ):

            status = equipment.get(
                "operational_status",
                "",
            )


            if (
                isinstance(
                    status,
                    str,
                )
                and
                status.upper()
                == "OUT_OF_SERVICE"
            ):

                decisions.append(
                    {
                        "type":
                            "equipment",

                        "priority":
                            "HIGH",

                        "action":
                            "schedule_equipment_maintenance",

                        "title":
                            f"Review equipment {equipment_id}",

                        "details":
                            {
                                "equipment_id":
                                    equipment_id,

                                "equipment":
                                    equipment,
                            },
                    }
                )



    def _check_equipment_visibility(
        self,
        equipment_status,
        decisions,
    ):
        """
        Detect missing equipment operational visibility.
        """

        if not equipment_status:

            decisions.append(
                {
                    "type":
                        "equipment",

                    "priority":
                        "WARNING",

                    "action":
                        "record_equipment_activity",

                    "title":
                        "Equipment operational data unavailable",

                    "details":
                        {},
                }
            )
