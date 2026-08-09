from dataclasses import dataclass
from datetime import datetime


@dataclass
class DifferentialAssessment:

    animal_id: str

    possible_condition: str

    likelihood: str

    supporting_observations: str

    veterinarian_notes: str

    assessed_by: str

    assessed_at: datetime
