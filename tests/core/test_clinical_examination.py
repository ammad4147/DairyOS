from dairyos.herd.health.services.clinical_examination_service import (
    ClinicalExaminationService
)



def test_examination_animal():

    result = ClinicalExaminationService().examine(

        "HF-2002",

        "39.5",

        "30",

        "80",

        "3",

        "Udder swelling",

        "Veterinarian"

    )

    assert result.animal_id == "HF-2002"



def test_temperature():

    result = ClinicalExaminationService().examine(

        "HF-2002",

        "39.5",

        "30",

        "80",

        "3",

        "Normal",

        "Vet"

    )

    assert result.temperature == "39.5"



def test_examiner():

    result = ClinicalExaminationService().examine(

        "HF-2002",

        "39",

        "28",

        "75",

        "3",

        "Normal",

        "Dr Ahmed"

    )

    assert result.examiner == "Dr Ahmed"
