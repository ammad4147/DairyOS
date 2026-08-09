from dataclasses import dataclass


@dataclass
class ClinicalCompleteness:

    animal_id: str

    completed_items: list

    missing_items: list

    complete: bool
