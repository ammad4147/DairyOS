from dataclasses import dataclass


@dataclass
class DiagnosticEvidence:

    animal_id: str

    test_name: str

    sample_type: str

    requested_by: str

    reason: str

    status: str
