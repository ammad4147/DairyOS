from dairyos.intelligence.kernel.context.intelligence_context import (
    IntelligenceContext,
)

from dairyos.intelligence.kernel.assessment.situation_assessment import (
    SituationAssessment,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)


def test_situation_assessment_detects_operational_pressure():

    context = IntelligenceContext()

    context.add_signal(
        IntelligenceSignal(
            source="health",
            category="animal_health",
            message="Critical temperature alert",
            severity="critical",
        )
    )

    assessment = SituationAssessment()

    result = assessment.assess(context)

    assert result["signal_count"] == 1
    assert result["highest_severity"] == "critical"
    assert result["operational_pressure"] == "elevated"
