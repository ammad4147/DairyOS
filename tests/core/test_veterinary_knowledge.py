from dairyos.herd.health.services.veterinary_knowledge_service import (
    VeterinaryKnowledgeService
)



def test_mastitis_reference():

    result = VeterinaryKnowledgeService().find_by_symptom(

        "Milk reduction"

    )

    assert len(result) > 0



def test_condition_name():

    result = VeterinaryKnowledgeService().find_by_symptom(

        "Udder swelling"

    )

    assert result[0].disease_name == "Mastitis"



def test_diagnostic_reference():

    result = VeterinaryKnowledgeService().find_by_symptom(

        "Reduced appetite"

    )

    assert len(result[0].diagnostic_methods) > 0
