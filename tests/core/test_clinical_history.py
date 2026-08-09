from dairyos.herd.health.services.clinical_history_service import (
    ClinicalHistoryService
)



def test_history_animal():

    result = ClinicalHistoryService().record(

        "HF-2001",

        "Reduced milk production",

        "Previous mastitis",

        "Antibiotic treatment",

        "Normal calving history",

        "Reduced feed intake",

        "Veterinarian"

    )

    assert result.animal_id == "HF-2001"



def test_history_complaint():

    result = ClinicalHistoryService().record(

        "HF-2001",

        "Fever",

        "",

        "",

        "",

        "",

        "Vet"

    )

    assert result.complaint == "Fever"



def test_history_creator():

    result = ClinicalHistoryService().record(

        "HF-2001",

        "Issue",

        "",

        "",

        "",

        "",

        "Dr Ali"

    )

    assert result.created_by == "Dr Ali"
