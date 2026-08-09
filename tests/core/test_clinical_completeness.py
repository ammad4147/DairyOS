from dairyos.herd.health.services.clinical_completeness_service import (
    ClinicalCompletenessService
)



def test_missing_information_detected():

    result = ClinicalCompletenessService().review(

        "HF-5001",

        [

            "Observation",

            "History"

        ]

    )


    assert result.complete is False



def test_complete_case():

    result = ClinicalCompletenessService().review(

        "HF-5001",

        [

            "Observation",

            "History",

            "Examination",

            "Differential Assessment",

            "Diagnostic Plan"

        ]

    )


    assert result.complete is True



def test_missing_items_visible():

    result = ClinicalCompletenessService().review(

        "HF-5001",

        [

            "Observation"

        ]

    )


    assert "History" in result.missing_items
