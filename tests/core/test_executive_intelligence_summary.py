from dairyos.herd.dashboard.services.executive_intelligence_summary_service import ExecutiveIntelligenceSummaryService



def test_summary_creation():

    summary = ExecutiveIntelligenceSummaryService().generate(

        "STABLE",

        "No concern",

        "Continue monitoring",

        []

    )

    assert summary.farm_status == "STABLE"



def test_concern():

    summary = ExecutiveIntelligenceSummaryService().generate(

        "WARNING",

        "Production decline risk",

        "Review feed quality",

        [

            "Review ration"

        ]

    )

    assert summary.top_concern == "Production decline risk"



def test_recommendation():

    summary = ExecutiveIntelligenceSummaryService().generate(

        "WARNING",

        "Risk",

        "Review feed quality",

        [

            "Action"

        ]

    )

    assert summary.recommended_focus == "Review feed quality"



def test_actions():

    summary = ExecutiveIntelligenceSummaryService().generate(

        "WARNING",

        "Risk",

        "Action",

        [

            "Review feed",

            "Check health"

        ]

    )

    assert len(summary.priority_actions) == 2



def test_owner_attention_required():

    summary = ExecutiveIntelligenceSummaryService().generate(

        "WARNING",

        "Risk",

        "Action",

        [

            "Review"

        ]

    )

    assert summary.owner_attention



def test_stable_no_actions():

    summary = ExecutiveIntelligenceSummaryService().generate(

        "STABLE",

        "None",

        "Monitor",

        []

    )

    assert not summary.owner_attention



def test_attention_service():

    service = ExecutiveIntelligenceSummaryService()

    summary = service.generate(

        "WARNING",

        "Risk",

        "Action",

        [

            "Review"

        ]

    )

    assert service.requires_owner_attention(summary)



def test_multiple_actions():

    summary = ExecutiveIntelligenceSummaryService().generate(

        "WARNING",

        "Risk",

        "Action",

        [

            "A",

            "B",

            "C"

        ]

    )

    assert len(summary.priority_actions) == 3



def test_model_fields():

    summary = ExecutiveIntelligenceSummaryService().generate(

        "STABLE",

        "None",

        "Monitor",

        []

    )

    assert summary.recommended_focus == "Monitor"



def test_summary_type():

    summary = ExecutiveIntelligenceSummaryService().generate(

        "STABLE",

        "None",

        "Monitor",

        []

    )

    assert isinstance(summary.priority_actions, list)
