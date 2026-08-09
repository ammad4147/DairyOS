from dairyos.application.dashboard.models.dashboard_activity import (
    DashboardActivity,
)


class EventDashboardAdapter:
    """
    Converts DairyOS operational events
    into dashboard read models.

    Supports:

    - database operational events
    - runtime event timeline
    - event repositories
    """


    def __init__(
        self,
        event_repository=None,
        operations_runtime=None,
    ):

        self.event_repository = event_repository

        self.operations_runtime = operations_runtime



    def get_activities(
        self,
    ):

        activities = []


        events = []


        if self.operations_runtime is not None:

            events.extend(
                self.operations_runtime
                .get_events()
            )


        if self.event_repository is not None:

            events.extend(
                self.event_repository
                .get_all()
            )


        for event in events:


            if isinstance(event, dict):

                activities.append(

                    DashboardActivity(

                        event_type=(
                            event.get(
                                "event_type",
                                "unknown",
                            )
                        ),

                        source=(
                            event.get(
                                "operator",
                                "system",
                            )
                        ),

                        description=str(
                            event.get(
                                "payload",
                                {},
                            )
                        ),

                        timestamp=(
                            event.get(
                                "timestamp"
                            )
                        ),
                    )
                )


                continue



            if hasattr(
                event,
                "created_at",
            ):

                activities.append(

                    DashboardActivity(

                        event_type=event.event_type,

                        source=event.source,

                        description=event.description,

                        timestamp=event.created_at,

                    )
                )


            else:

                activities.append(

                    DashboardActivity(

                        event_type=event.event_type,

                        source=event.operator,

                        description=str(
                            event.payload.get(
                                "description",
                                event.event_type,
                            )
                        ),

                        timestamp=event.timestamp,

                    )
                )


        return activities
