from dataclasses import dataclass



@dataclass
class StaffTask:


    task_id: str

    task_name: str

    assigned_team: str

    priority: str

    status: str

    action: str
