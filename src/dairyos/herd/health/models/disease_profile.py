from dataclasses import dataclass


@dataclass
class DiseaseProfile:

    disease_name: str

    category: str

    species: str

    common_signs: list

    diagnostic_methods: list

    prevention_notes: str

    treatment_reference: str

    source_reference: str
