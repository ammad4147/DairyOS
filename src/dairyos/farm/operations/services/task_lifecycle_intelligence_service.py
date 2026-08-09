from datetime import datetime, timezone


class TaskLifecycleIntelligenceService:
    """
    Evaluates task lifecycle condition.

    Reads operational task state.

    Does not:
        - create tasks
        - modify tasks
        - complete tasks
        - change FarmOperationalState

    Provides awareness only.
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


        evaluations = []


        for task in state.open_tasks:

            evaluations.append(
                self._evaluate_task(
                    task
                )
            )


        return evaluations



    def summary(
        self,
    ):

        evaluations = (
            self.evaluate()
        )


        return {

            "total_open_tasks":
                len(
                    evaluations
                ),

            "overdue_tasks":
                len(
                    [
                        task
                        for task
                        in evaluations
                        if task[
                            "ageing_status"
                        ]
                        == "OVERDUE"
                    ]
                ),

            "attention_required":
                len(
                    [
                        task
                        for task
                        in evaluations
                        if task[
                            "requires_attention"
                        ]
                    ]
                ),

            "tasks":
                evaluations,

        }



    def _evaluate_task(
        self,
        task,
    ):

        now = datetime.now(
            timezone.utc
        )


        created_at = (
            task.get(
                "created_at"
            )
        )


        due_date = (
            task.get(
                "due_date"
            )
        )


        age_days = 0


        if isinstance(
            created_at,
            datetime,
        ):

            age_days = (
                now - created_at
            ).days



        ageing_status = (
            "ACTIVE"
        )


        if due_date is not None:

            if isinstance(
                due_date,
                datetime,
            ):

                if due_date < now:

                    ageing_status = (
                        "OVERDUE"
                    )


            elif isinstance(
                due_date,
                str,
            ):

                try:

                    parsed_due_date = (
                        datetime.fromisoformat(
                            due_date
                        )
                    )


                    if parsed_due_date < now:

                        ageing_status = (
                            "OVERDUE"
                        )


                except ValueError:

                    pass



        priority = task.get(
            "priority",
            "NORMAL",
        )


        requires_attention = (

            ageing_status
            ==
            "OVERDUE"

            or

            priority
            in
            (
                "HIGH",
                "CRITICAL",
            )

        )



        return {

            "task_id":
                task.get(
                    "task_id"
                ),

            "description":
                task.get(
                    "description",
                    "",
                ),

            "assigned_to":
                task.get(
                    "assigned_to"
                ),

            "priority":
                priority,

            "age_days":
                age_days,

            "ageing_status":
                ageing_status,

            "requires_attention":
                requires_attention,

            "status":
                task.get(
                    "status",
                    "OPEN",
                ),

        }
