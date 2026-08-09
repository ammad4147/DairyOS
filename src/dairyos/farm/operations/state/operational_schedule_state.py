from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class OperationalScheduleState:
    """
    Planned operational schedule state.

    Represents what should happen.

    Does NOT create actual farm data.

    Actual execution remains manually entered.

    Awareness:
    - Detects missing execution.
    - Generates heads-up notifications.
    - Never completes activities automatically.
    """

    schedule_date: str

    created_at: datetime = field(
        default_factory=lambda:
        datetime.now(timezone.utc)
    )

    milking_schedule: list = field(
        default_factory=list
    )

    feeding_schedule: list = field(
        default_factory=list
    )

    health_schedule: list = field(
        default_factory=list
    )

    breeding_schedule: list = field(
        default_factory=list
    )

    task_schedule: list = field(
        default_factory=list
    )

    completed_milking_sessions: list = field(
        default_factory=list
    )

    completed_feeding_sessions: list = field(
        default_factory=list
    )

    completed_health_events: list = field(
        default_factory=list
    )

    completed_breeding_events: list = field(
        default_factory=list
    )

    completed_tasks: list = field(
        default_factory=list
    )


    def add_milking_session(
        self,
        session: dict,
    ):

        self.milking_schedule.append(
            session
        )


    def add_feeding_schedule(
        self,
        feeding: dict,
    ):

        self.feeding_schedule.append(
            feeding
        )


    def add_health_schedule(
        self,
        activity: dict,
    ):

        self.health_schedule.append(
            activity
        )


    def add_breeding_schedule(
        self,
        activity: dict,
    ):

        self.breeding_schedule.append(
            activity
        )


    def add_task_schedule(
        self,
        task: dict,
    ):

        self.task_schedule.append(
            task
        )


    def complete_milk_checkpoint(
        self,
        shift: str,
    ):

        if shift not in self.completed_milking_sessions:

            self.completed_milking_sessions.append(
                shift
            )


    def complete_feed_checkpoint(
        self,
        feed_type: str,
    ):

        if feed_type not in self.completed_feeding_sessions:

            self.completed_feeding_sessions.append(
                feed_type
            )


    def complete_health_checkpoint(
        self,
        event_id: str,
    ):

        if event_id not in self.completed_health_events:

            self.completed_health_events.append(
                event_id
            )


    def complete_breeding_checkpoint(
        self,
        event_id: str,
    ):

        if event_id not in self.completed_breeding_events:

            self.completed_breeding_events.append(
                event_id
            )


    def complete_task_checkpoint(
        self,
        task_id: str,
    ):

        if task_id not in self.completed_tasks:

            self.completed_tasks.append(
                task_id
            )


    def pending_milk_sessions(
        self,
    ):

        return [
            session.get("shift")
            for session in self.milking_schedule
            if session.get("shift")
            not in self.completed_milking_sessions
        ]


    def pending_feed_sessions(
        self,
    ):

        return [
            session.get("feed_type")
            for session in self.feeding_schedule
            if session.get("feed_type")
            not in self.completed_feeding_sessions
        ]


    def evaluate_heads_up(
        self,
    ):

        notifications = []


        for shift in self.pending_milk_sessions():

            notifications.append(
                {
                    "type": "milking_pending",
                    "shift": shift,
                    "message":
                        f"Milking session {shift} has not been recorded.",
                }
            )


        for feed_type in self.pending_feed_sessions():

            notifications.append(
                {
                    "type": "feeding_pending",
                    "feed_type": feed_type,
                    "message":
                        f"Feeding activity {feed_type} has not been recorded.",
                }
            )


        for health in self.health_schedule:

            event_id = health.get(
                "event_id"
            )

            if event_id not in self.completed_health_events:

                notifications.append(
                    {
                        "type": "health_pending",
                        "event_id": event_id,
                        "message":
                            "Scheduled health activity has not been recorded.",
                        "due_time":
                            health.get("due_time"),
                    }
                )


        for breeding in self.breeding_schedule:

            event_id = breeding.get(
                "event_id"
            )

            if event_id not in self.completed_breeding_events:

                notifications.append(
                    {
                        "type": "breeding_pending",
                        "event_id": event_id,
                        "message":
                            "Scheduled breeding activity has not been recorded.",
                        "due_time":
                            breeding.get("due_time"),
                    }
                )


        for task in self.task_schedule:

            task_id = task.get(
                "task_id"
            )

            if task_id not in self.completed_tasks:

                notifications.append(
                    {
                        "type": "task_pending",
                        "task_id": task_id,
                        "message":
                            "Scheduled task has not been completed.",
                        "due_time":
                            task.get("due_time"),
                    }
                )


        return notifications


    def summary(
        self,
    ):

        return {

            "schedule_date":
                self.schedule_date,

            "milking_sessions":
                len(self.milking_schedule),

            "feeding_events":
                len(self.feeding_schedule),

            "health_events":
                len(self.health_schedule),

            "breeding_events":
                len(self.breeding_schedule),

            "tasks":
                len(self.task_schedule),

            "pending_milk_sessions":
                len(self.pending_milk_sessions()),

            "pending_feed_sessions":
                len(self.pending_feed_sessions()),

            "heads_up_count":
                len(self.evaluate_heads_up()),

        }
