from dairyos.herd.health.services.treatment_plan_service import (
    TreatmentPlanService
)



def test_treatment_animal():

    result = TreatmentPlanService().create(

        "HF-4002",

        "Mastitis",

        "Medication",

        "As prescribed",

        "5 days",

        "Veterinarian"

    )

    assert result.animal_id == "HF-4002"



def test_treatment_status():

    result = TreatmentPlanService().create(

        "HF-4002",

        "Mastitis",

        "Treatment",

        "Instruction",

        "7 days",

        "Vet"

    )

    assert result.status == "ACTIVE"



def test_responsible_person():

    result = TreatmentPlanService().create(

        "HF-4002",

        "Infection",

        "Therapy",

        "Instruction",

        "3 days",

        "Dr Ahmed"

    )

    assert result.responsible_person == "Dr Ahmed"
