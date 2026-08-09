from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class WorkforceIntelligenceService:
    """
    Operational intelligence for farm workforce execution.

    Converts workforce operational state into
    actionable attention items.

    This is rule-based operational awareness.

    Rules:
    - Reads FarmOperationalState only.
    - Does not modify operational facts.
    - Does not manage employees.
    - Does not implement HR, payroll, or attendance policy.

    Workforce execution truth remains inside:
        FarmOperationalState
    """



    def evaluate(
        self,
        state: FarmOperationalState,
    ) -> list[dict]:
        """
        Evaluate workforce operational condition.

        Returns operational attention items.
        """

        decisions = []


        workforce = (
            state.workforce_status
            if state.workforce_status
            else {}
        )


        self._check_pending_tasks(
            workforce,
            decisions,
        )


        self._check_overdue_tasks(
            workforce,
            decisions,
        )


        self._check_workload_level(
            workforce,
            decisions,
        )


        self._check_activity_availability(
            workforce,
            decisions,
        )


        return decisions



    def _check_pending_tasks(
        self,
        workforce,
        decisions,
    ):
        """
        Detect pending workforce workload.
        """

        pending_tasks = workforce.get(
            "pending_tasks",
            0,
        )


        if pending_tasks:

            decisions.append(
                {
                    "type":
                        "workforce",

                    "priority":
                        "NORMAL",

                    "action":
                        "review_workforce_load",

                    "title":
                        "Pending workforce workload",

                    "details":
                        {
                            "pending_tasks":
                                pending_tasks,
                        },
                }
            )



    def _check_overdue_tasks(
        self,
        workforce,
        decisions,
    ):
        """
        Detect overdue operational duties.
        """

        overdue_tasks = workforce.get(
            "overdue_tasks",
            0,
        )


        if overdue_tasks:

            decisions.append(
                {
                    "type":
                        "workforce",

                    "priority":
                        "HIGH",

                    "action":
                        "review_overdue_workforce_tasks",

                    "title":
                        "Overdue workforce tasks",

                    "details":
                        {
                            "overdue_tasks":
                                overdue_tasks,
                        },
                }
            )



    def _check_workload_level(
        self,
        workforce,
        decisions,
    ):
        """
        Detect workforce capacity risk.
        """

        workload_level = workforce.get(
            "workload_level",
            "",
        )


        if (
            isinstance(
                workload_level,
                str,
            )

            and

            workload_level.upper()
            ==
            "HIGH"
        ):

            decisions.append(
                {
                    "type":
                        "workforce",

                    "priority":
                        "HIGH",

                    "action":
                        "review_workforce_capacity",

                    "title":
                        "Workforce workload capacity risk",

                    "details":
                        {
                            "workload_level":
                                workload_level,
                        },
                }
            )



    def _check_activity_availability(
        self,
        workforce,
        decisions,
    ):
        """
        Detect missing workforce operational visibility.
        """

        if not workforce:

            decisions.append(
                {
                    "type":
                        "workforce",

                    "priority":
                        "WARNING",

                    "action":
                        "record_workforce_activity",

                    "title":
                        "Workforce activity data unavailable",

                    "details":
                        {},
                }
            )
