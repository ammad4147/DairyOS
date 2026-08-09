from dataclasses import dataclass



@dataclass
class AlertAssignment:

    alert_id: str

    assigned_to: str

    role: str

