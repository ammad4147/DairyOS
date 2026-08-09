from dairyos.herd.health.services.veterinary_knowledge_service import (
    VeterinaryKnowledgeService
)



def test_database_loaded():

    service = VeterinaryKnowledgeService()

    assert service.disease_count() >= 3



def test_mastitis_search():

    service = VeterinaryKnowledgeService()

    result = service.find_disease(

        "Mastitis"

    )


    assert len(result) == 1

    assert "Udder swelling" in result[0].common_signs



def test_symptom_search():

    service = VeterinaryKnowledgeService()

    result = service.search_symptom(

        "Milk yield reduction"

    )


    assert len(result) == 1



def test_symptom_has_checks():

    service = VeterinaryKnowledgeService()

    result = service.search_symptom(

        "Udder swelling"

    )


    assert (

        "Veterinary examination"

        in

        result[0].recommended_checks

    )
