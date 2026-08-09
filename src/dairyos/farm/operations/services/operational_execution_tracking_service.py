from datetime import datetime, timezone


class OperationalExecutionTrackingService:
    """
    Operational execution awareness service.

    Compares planned operational schedules
    against manually recorded operational events.

    Rules:
    - Reads operational state only.
    - Reads timeline events only.
    - Generates execution intelligence.
    - Does not create operational data.
    - Does not complete activities automatically.
    - Does not modify FarmOperationalState.
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


        executions = []


        executions.extend(
            self._evaluate_activity_group(
                activity_type="MILKING",
                schedules=(
                    state.schedule_state
                    .milking_schedule
                ),
                timeline=timeline,
                event_types=[
                    "milk_recorded",
                    "milk_activity_recorded",
                ],
                reference_key="shift",
            )
        )


        executions.extend(
            self._evaluate_activity_group(
                activity_type="FEEDING",
                schedules=(
                    state.schedule_state
                    .feeding_schedule
                ),
                timeline=timeline,
                event_types=[
                    "feed_distributed",
                    "feed_recorded",
                ],
                reference_key="feed_type",
            )
        )


        executions.extend(
            self._evaluate_activity_group(
                activity_type="HEALTH",
                schedules=(
                    state.schedule_state
                    .health_schedule
                ),
                timeline=timeline,
                event_types=[
                    "health_observation_recorded",
                    "health_recorded",
                ],
                reference_key="event_id",
            )
        )


        executions.extend(
            self._evaluate_activity_group(
                activity_type="BREEDING",
                schedules=(
                    state.schedule_state
                    .breeding_schedule
                ),
                timeline=timeline,
                event_types=[
                    "breeding_activity_recorded",
                    "breeding_recorded",
                ],
                reference_key="event_id",
            )
        )


        executions.extend(
            self._evaluate_activity_group(
                activity_type="TASK",
                schedules=(
                    state.schedule_state
                    .task_schedule
                ),
                timeline=timeline,
                event_types=[
                    "task_created",
                    "task_completed",
                ],
                reference_key="task_id",
            )
        )


        return executions



    def summary(
        self,
    ):

        executions = (
            self.evaluate()
        )


        return {

            "total_activities":
                len(executions),

            "completed":
                len(
                    [
                        item
                        for item in executions
                        if item["status"]
                        ==
                        "COMPLETED_ON_TIME"
                    ]
                ),

            "pending":
                len(
                    [
                        item
                        for item in executions
                        if item["status"]
                        ==
                        "MISSED"
                    ]
                ),

            "activities":
                executions,

        }



    def _evaluate_activity_group(
        self,
        activity_type,
        schedules,
        timeline,
        event_types,
        reference_key,
    ):

        results = []


        for schedule in schedules:

            reference = (
                schedule.get(
                    reference_key
                )
            )


            found = False


            for event in timeline:

                if event.get(
                    "event_type"
                ) not in event_types:

                    continue


                payload = (
                    event.get(
                        "payload",
                        {}
                    )
                )


                if (
                    payload.get(
                        reference_key
                    )
                    ==
                    reference
                ):

                    found = True
                    break



            results.append(

                {

                    "activity_type":
                        activity_type,

                    "reference":
                        reference,

                    "status":
                        (
                            "COMPLETED_ON_TIME"
                            if found
                            else "MISSED"
                        ),

                }

            )


        return results
