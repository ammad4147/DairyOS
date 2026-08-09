from dairyos.intelligence.engine.intelligence_engine import (
    IntelligenceEngine,
)

from dairyos.intelligence.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.models.intelligence_recommendation import (
    IntelligenceRecommendation,
)


def test_intelligence_engine_registers_signal_and_recommendation():

    engine = IntelligenceEngine()


    signal = IntelligenceSignal(

        signal_type="MILK_VARIANCE",

        severity="WARNING",

        source="milk_production",

    )


    recommendation = IntelligenceRecommendation(

        recommendation_type="REVIEW_MILK",

        priority="HIGH",

        source_signal="MILK_VARIANCE",

        action="Review milk production",

    )


    engine.register_signal(
        signal
    )

    engine.register_recommendation(
        recommendation
    )


    assert len(engine.get_signals()) == 1

    assert len(engine.get_recommendations()) == 1


    summary = engine.summary()


    assert summary["signal_count"] == 1

    assert summary["recommendation_count"] == 1

