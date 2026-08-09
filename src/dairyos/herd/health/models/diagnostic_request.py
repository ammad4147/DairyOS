from dataclasses import dataclass
from datetime import datetime


@dataclass
class DiagnosticRequest:

    animal_id: str

    test_type: str

    reason: str

    requested_by: str

    priority: str

    status: str

    requested_at: datetime
