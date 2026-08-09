from dataclasses import dataclass
from datetime import datetime


@dataclass
class TreatmentResponse:

    animal_id: str

    treatment_reference: str

    observation: str

    response_status: str

    recorded_at: datetime
