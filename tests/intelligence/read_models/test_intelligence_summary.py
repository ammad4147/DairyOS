from dairyos.intelligence.read_models.intelligence_summary import (
    IntelligenceSummary,
)


def test_intelligence_summary_projects_pipeline_result():

    result = {

        "signals": [],

        "recommendations": [],

    }


    summary = (
        IntelligenceSummary
        .from_pipeline_result(
            result
        )
    )


    assert summary.signal_count == 0

    assert summary.critical_signal_count == 0

    assert summary.warning_signal_count == 0
