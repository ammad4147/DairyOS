from dairyos.herd.health.services.diagnosis_service import (
    DiagnosisService
)



def test_diagnosis_animal():

    result = DiagnosisService().record(

        "HF-4001",

        "Mastitis",

        "CONFIRMED",

        "HIGH",

        "Veterinarian"

    )

    assert result.animal_id == "HF-4001"



def test_diagnosis_name():

    result = DiagnosisService().record(

        "HF-4001",

        "Mastitis",

        "CONFIRMED",

        "HIGH",

        "Vet"

    )

    assert result.diagnosis == "Mastitis"



def test_diagnosis_author():

    result = DiagnosisService().record(

        "HF-4001",

        "Ketosis",

        "SUSPECTED",

        "MEDIUM",

        "Dr Ali"

    )

    assert result.diagnosed_by == "Dr Ali"
