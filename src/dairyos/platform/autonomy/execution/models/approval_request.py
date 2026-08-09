from dataclasses import dataclass



@dataclass
class ApprovalRequest:

    action_id: str

    requested_by: str

    approved_by: str | None = None

    status: str = "pending"

