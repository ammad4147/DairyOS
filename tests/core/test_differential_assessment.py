from dairyos.herd.health.services.differential_assessment_service import (
    DifferentialAssessmentService
)



def test_assessment_animal():

    result = DifferentialAssessmentService().assess(

        "HF-3001",

        "Mastitis",

        "HIGH",

        "Milk reduction and udder swelling",

        "Further examination required",

        "Veterinarian"

    )

    assert result.animal_id == "HF-3001"



def test_possible_condition():

    result = DifferentialAssessmentService().assess(

        "HF-3001",

        "Mastitis",

        "HIGH",

        "",

        "",

        "Vet"

    )

    assert result.possible_condition == "Mastitis"



def test_likelihood():

    result = DifferentialAssessmentService().assess(

        "HF-3001",

        "Ketosis",

        "MEDIUM",

        "",

        "",

        "Vet"

    )

    assert result.likelihood == "MEDIUM"
