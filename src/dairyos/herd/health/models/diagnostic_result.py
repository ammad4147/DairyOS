from dataclasses import dataclass


@dataclass
class DiagnosticResult:

    animal_id: str

    test_name: str

    result: str

    interpretation: str

    verified_by: str
