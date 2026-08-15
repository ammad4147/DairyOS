from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from dairyos.milk.models.milking_cycle import (
    DEFAULT_SESSION_TIMES,
    MilkingCycle,
    MilkingFrequency,
    classify_session_entry,
)


@dataclass
class OperationalScheduleState:
    """Planned operational schedule state; actual execution remains manual."""

    schedule_date: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    milking_schedule: list = field(default_factory=list)
    milking_cycles: dict = field(default_factory=dict)
    feeding_schedule: list = field(default_factory=list)
    health_schedule: list = field(default_factory=list)
    breeding_schedule: list = field(default_factory=list)
    task_schedule: list = field(default_factory=list)
    completed_milking_sessions: list = field(default_factory=list)
    completed_feeding_sessions: list = field(default_factory=list)
    completed_health_events: list = field(default_factory=list)
    completed_breeding_events: list = field(default_factory=list)
    completed_tasks: list = field(default_factory=list)

    def add_milking_session(self, session: dict):
        self.milking_schedule.append(session)

    def configure_milking_cycle(self, animal_id: str, frequency: int | MilkingFrequency, effective_from: str | date, session_times=None) -> MilkingCycle:
        if isinstance(effective_from, str):
            effective_from = date.fromisoformat(effective_from)
        cycle = MilkingCycle(
            animal_id=str(animal_id),
            frequency=MilkingFrequency(int(frequency)),
            effective_from=effective_from,
            session_times=session_times if session_times is not None else DEFAULT_SESSION_TIMES.copy(),
        )
        self.milking_cycles[str(animal_id)] = cycle
        return cycle

    def schedule_milking_cycles_for_date(self, operational_date: str | date) -> list:
        if isinstance(operational_date, str):
            operational_date = date.fromisoformat(operational_date)
        generated = []
        existing_keys = {(item.get("animal_id"), item.get("operational_date"), item.get("shift")) for item in self.milking_schedule}
        for cycle in self.milking_cycles.values():
            for session in cycle.expected_sessions(operational_date):
                key = (session["animal_id"], session["operational_date"], session["shift"])
                if key not in existing_keys:
                    self.milking_schedule.append(session)
                    generated.append(session)
                    existing_keys.add(key)
        return generated

    def expected_milking_session_count(self, animal_id: str, operational_date: str | date) -> int:
        cycle = self.milking_cycles.get(str(animal_id))
        if cycle is None:
            return 0
        if isinstance(operational_date, str):
            operational_date = date.fromisoformat(operational_date)
        return len(cycle.expected_sessions(operational_date))

    def record_milking_session(self, animal_id: str, operational_date: str | date, shift: str, status: str, reason: str | None = None, recorded_at: datetime | None = None) -> dict:
        if isinstance(operational_date, str):
            operational_date = date.fromisoformat(operational_date)
        status = str(status).upper()
        if status not in {"RECORDED", "NOT_MILKED"}:
            raise ValueError("status must be RECORDED or NOT_MILKED")
        if status == "NOT_MILKED" and not str(reason or "").strip():
            raise ValueError("NOT_MILKED requires a reason")
        cycle = self.milking_cycles.get(str(animal_id))
        expected = cycle.expected_session(operational_date, shift) if cycle else None
        if expected is None:
            raise ValueError(f"no expected milking session for animal {animal_id} on {operational_date.isoformat()} shift {shift}")
        recorded_at = recorded_at or datetime.now(timezone.utc)
        if recorded_at.tzinfo is None:
            recorded_at = recorded_at.replace(tzinfo=timezone.utc)
        if status == "RECORDED":
            outcome = classify_session_entry(expected, recorded_at)
        else:
            outcome = {
                **expected,
                "status": "NOT_MILKED",
                "reason": reason,
                "recorded_at": recorded_at.isoformat(),
                "late": recorded_at > datetime.fromisoformat(expected["scheduled_at"]),
            }

        completed_keys = {
            (item.get("animal_id"), item.get("operational_date"), item.get("shift"))
            for item in self.completed_milking_sessions
            if isinstance(item, dict)
        }
        missed_prior = []
        for pending in self.pending_milk_sessions(str(animal_id), operational_date):
            scheduled_at = datetime.fromisoformat(pending["scheduled_at"])
            if scheduled_at < recorded_at and (pending["animal_id"], pending["operational_date"], pending["shift"]) not in completed_keys:
                missed_prior.append(pending["shift"])
        if missed_prior:
            outcome["missed_prior_sessions"] = missed_prior
            outcome["notifications"] = [
                {
                    "type": "MISSED_MILKING_SESSION",
                    "animal_id": str(animal_id),
                    "date": operational_date.isoformat(),
                    "shift": missed,
                }
                for missed in missed_prior
            ]

        key = (str(animal_id), operational_date.isoformat(), shift)
        self.completed_milking_sessions = [
            item for item in self.completed_milking_sessions
            if not (isinstance(item, dict) and (item.get("animal_id"), item.get("operational_date"), item.get("shift")) == key)
        ]
        self.completed_milking_sessions.append(outcome)
        return outcome

    def pending_milk_sessions(self, animal_id: str | None = None, operational_date: str | date | None = None):
        target_date = operational_date.isoformat() if isinstance(operational_date, date) else operational_date
        completed_keys = {
            (item.get("animal_id"), item.get("operational_date"), item.get("shift"))
            for item in self.completed_milking_sessions
            if isinstance(item, dict)
        }
        completed_legacy = {item for item in self.completed_milking_sessions if isinstance(item, str)}
        pending = []
        for session in self.milking_schedule:
            if animal_id is not None and session.get("animal_id") != str(animal_id):
                continue
            if target_date is not None and session.get("operational_date", self.schedule_date) != target_date:
                continue
            if session.get("animal_id") is None and session.get("shift") in completed_legacy:
                continue
            key = (session.get("animal_id"), session.get("operational_date", self.schedule_date), session.get("shift"))
            if key not in completed_keys:
                pending.append(session)
        return pending

    def is_milking_date_complete(self, operational_date: str | date | None = None) -> bool:
        target_date = operational_date.isoformat() if isinstance(operational_date, date) else operational_date or self.schedule_date
        relevant = [s for s in self.milking_schedule if s.get("operational_date", self.schedule_date) == target_date]
        if not relevant:
            return False
        return not self.pending_milk_sessions(operational_date=target_date)

    def add_feeding_schedule(self, feeding: dict):
        self.feeding_schedule.append(feeding)

    def add_health_schedule(self, activity: dict):
        self.health_schedule.append(activity)

    def add_breeding_schedule(self, activity: dict):
        self.breeding_schedule.append(activity)

    def add_task_schedule(self, task: dict):
        self.task_schedule.append(task)

    def complete_milk_checkpoint(self, shift: str):
        if shift not in self.completed_milking_sessions:
            self.completed_milking_sessions.append(shift)

    def complete_feed_checkpoint(self, feed_type: str):
        if feed_type not in self.completed_feeding_sessions:
            self.completed_feeding_sessions.append(feed_type)

    def complete_health_checkpoint(self, event_id: str):
        if event_id not in self.completed_health_events:
            self.completed_health_events.append(event_id)

    def complete_breeding_checkpoint(self, event_id: str):
        if event_id not in self.completed_breeding_events:
            self.completed_breeding_events.append(event_id)

    def complete_task_checkpoint(self, task_id: str):
        if task_id not in self.completed_tasks:
            self.completed_tasks.append(task_id)

    def pending_feed_sessions(self):
        return [session.get("feed_type") for session in self.feeding_schedule if session.get("feed_type") not in self.completed_feeding_sessions]

    def evaluate_heads_up(self):
        notifications = []
        for session in self.pending_milk_sessions():
            notifications.append({
                "type": "milking_pending",
                "animal_id": session.get("animal_id"),
                "date": session.get("operational_date", self.schedule_date),
                "shift": session.get("shift"),
                "message": f"Milking session {session.get('shift')} has not been recorded.",
            })
        for feed_type in self.pending_feed_sessions():
            notifications.append({"type": "feeding_pending", "feed_type": feed_type, "message": f"Feeding activity {feed_type} has not been recorded."})
        for health in self.health_schedule:
            event_id = health.get("event_id")
            if event_id not in self.completed_health_events:
                notifications.append({"type": "health_pending", "event_id": event_id, "message": "Scheduled health activity has not been recorded.", "due_time": health.get("due_time")})
        for breeding in self.breeding_schedule:
            event_id = breeding.get("event_id")
            if event_id not in self.completed_breeding_events:
                notifications.append({"type": "breeding_pending", "event_id": event_id, "message": "Scheduled breeding activity has not been recorded.", "due_time": breeding.get("due_time")})
        for task in self.task_schedule:
            task_id = task.get("task_id")
            if task_id not in self.completed_tasks:
                notifications.append({"type": "task_pending", "task_id": task_id, "message": "Scheduled task has not been completed.", "due_time": task.get("due_time")})
        return notifications

    def summary(self):
        return {
            "schedule_date": self.schedule_date,
            "milking_sessions": len(self.milking_schedule),
            "milking_cycles": len(self.milking_cycles),
            "feeding_events": len(self.feeding_schedule),
            "health_events": len(self.health_schedule),
            "breeding_events": len(self.breeding_schedule),
            "tasks": len(self.task_schedule),
            "pending_milk_sessions": len(self.pending_milk_sessions()),
            "pending_feed_sessions": len(self.pending_feed_sessions()),
            "heads_up_count": len(self.evaluate_heads_up()),
        }
