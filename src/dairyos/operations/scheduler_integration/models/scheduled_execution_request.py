from dataclasses import dataclass


@dataclass
class ScheduledExecutionRequest:
    """
    Represents a scheduled farm activity
    ready for conversion into executable work.
    """

    shift_id: str

    task_name: str

    assigned_role: str
