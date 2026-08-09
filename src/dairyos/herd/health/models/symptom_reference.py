from dataclasses import dataclass


@dataclass
class SymptomReference:

    symptom: str

    related_conditions: list

    recommended_checks: list
