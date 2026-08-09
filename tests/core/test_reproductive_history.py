from datetime import date


from dairyos.herd.health.services.reproductive_history_service import (
    ReproductiveHistoryService
)

from dairyos.herd.health.services.fertility_review_service import (
    FertilityReviewService
)

from dairyos.herd.health.models.insemination_record import (
    InseminationRecord
)



def test_previous_reproductive_history():

    record = InseminationRecord(

        "HF-9001",

        date.today(),

        "SEXED",

        "SIRE-01",

        "AI Technician",

        1,

        "FAILED",

        "No conception"

    )


    result = ReproductiveHistoryService().add_insemination(

        record

    )


    assert result.semen_type == "SEXED"



def test_multiple_failures_detected():

    records = [

        InseminationRecord(

            "HF-9002",

            date.today(),

            "SEXED",

            "SIRE-01",

            "TECH",

            1,

            "FAILED",

            "No conception"

        ),

        InseminationRecord(

            "HF-9002",

            date.today(),

            "NORMAL",

            "SIRE-02",

            "TECH",

            2,

            "FAILED",

            "No conception"

        ),

        InseminationRecord(

            "HF-9002",

            date.today(),

            "NORMAL",

            "SIRE-03",

            "TECH",

            3,

            "FAILED",

            "No conception"

        )

    ]


    result = FertilityReviewService().review(records)


    assert result["review_required"] is True



def test_successful_case_no_escalation():

    records = [

        InseminationRecord(

            "HF-9003",

            date.today(),

            "SEXED",

            "SIRE-04",

            "TECH",

            1,

            "PREGNANT",

            ""

        )

    ]


    result = FertilityReviewService().review(records)


    assert result["review_required"] is False
