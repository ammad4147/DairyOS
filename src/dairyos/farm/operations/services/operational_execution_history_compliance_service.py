from datetime import datetime, timezone


class OperationalExecutionHistoryComplianceService:
    """
    Operational execution history and compliance intelligence.

    Reads:
        - operational state
        - operational timeline

    Provides:
        - execution history visibility
        - compliance status awareness
        - missed activity detection
        - operational discipline indicators

    Rules:
        - Does not create operational records.
        - Does not modify FarmOperationalState.
        - Does not complete activities automatically.
        - Awareness projection only.
    """


    def __init__(
        self,
        operational_state_service,
        operations_timeline_service,
    ):

        self.operational_state_service = (
            operational_state_service
        )

        self.operations_timeline_service = (
            operations_timeline_service
        )


    def evaluate(
        self,
    ):

        state = (
            self.operational_state_service
            .get_state()
        )

        timeline = (
            self.operations_timeline_service
            .get_timeline()
        )


        total_expected = (
            len(state.schedule_state.milking_schedule)
            +
            len(state.schedule_state.feeding_schedule)
            +
            len(state.schedule_state.health_schedule)
            +
            len(state.schedule_state.breeding_schedule)
            +
            len(state.schedule_state.task_schedule)
        )


        missed = []


        missed.extend(
            self._pending_schedule_items(
                state.schedule_state.milking_schedule,
                state.schedule_state.completed_milking_sessions,
                "shift",
                "MILKING",
            )
        )


        missed.extend(
            self._pending_schedule_items(
                state.schedule_state.feeding_schedule,
                state.schedule_state.completed_feeding_sessions,
                "feed_type",
                "FEEDING",
            )
        )


        missed.extend(
            self._pending_schedule_items(
                state.schedule_state.health_schedule,
                state.schedule_state.completed_health_events,
                "event_id",
                "HEALTH",
            )
        )


        missed.extend(
            self._pending_schedule_items(
                state.schedule_state.breeding_schedule,
                state.schedule_state.completed_breeding_events,
                "event_id",
                "BREEDING",
            )
        )


        missed.extend(
            self._pending_schedule_items(
                state.schedule_state.task_schedule,
                state.schedule_state.completed_tasks,
                "task_id",
                "TASK",
            )
        )


        compliance_status = (
            "COMPLIANT"
            if len(missed) == 0
            else "ATTENTION_REQUIRED"
        )


        return {

            "evaluation_time":
                datetime.now(
                    timezone.utc
                ),

            "compliance_status":
                compliance_status,

            "expected_activities":
                total_expected,

            "recorded_events":
                len(timeline),

            "missed_activities":
                len(missed),

            "execution_history_count":
                len(timeline),

            "missed_items":
                missed,

            "timeline":
                list(timeline),

        }



    def summary(
        self,
    ):

        result = (
            self.evaluate()
        )


        return {

            "compliance_status":
                result["compliance_status"],

            "expected_activities":
                result["expected_activities"],

            "recorded_events":
                result["recorded_events"],

            "missed_activities":
                result["missed_activities"],

        }



    def _pending_schedule_items(
        self,
        scheduled_items,
        completed_items,
        reference_key,
        activity_type,
    ):

        pending = []


        for item in scheduled_items:

            reference = item.get(
                reference_key
            )


            if reference not in completed_items:

                pending.append(
                    {
                        "activity_type":
                            activity_type,

                        "reference":
                            reference,

                        "status":
                            "NOT_EXECUTED",

                        "due_time":
                            item.get(
                                "due_time"
                            ),
                    }
                )


        return pending
