from dairyos.herd.health.services.clinical_knowledge_service import (
    ClinicalKnowledgeService
)

from dairyos.herd.health.services.clinical_review_service import (
    ClinicalReviewService
)



def test_mastitis_reference_found():

    service = ClinicalKnowledgeService()


    result = service.find_by_indicator(

        "milk_drop"

    )


    assert len(result) > 0



def test_review_generates_possible_conditions():

    knowledge = ClinicalKnowledgeService()


    result = ClinicalReviewService().review(

        [

            "milk_drop",

            "abnormal_milk"

        ],

        knowledge

    )


    assert "Mastitis" in result.possible_conditions



def test_checks_generated():

    knowledge = ClinicalKnowledgeService()


    result = ClinicalReviewService().review(

        [

            "feed_drop"

        ],

        knowledge

    )


    assert len(result.checks) > 0
