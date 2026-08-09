from dataclasses import dataclass


@dataclass
class ClinicalIndicator:

    indicator_name: str

    category: str

    description: str

    severity: str
