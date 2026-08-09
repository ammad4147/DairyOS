from dataclasses import dataclass


@dataclass
class BreedingOutcome:

    animal_id: str

    insemination_attempts: int

    successful_conceptions: int

    failed_attempts: int

    bull_service_used: bool

    outcome_notes: str
