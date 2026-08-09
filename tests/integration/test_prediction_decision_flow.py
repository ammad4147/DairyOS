"""
DairyOS Sprint 025

Prediction to Decision Validation
"""


def test_prediction_to_decision_components():

    from dairyos.intelligence.prediction.services.prediction_service import (
        PredictionService,
    )

    from dairyos.intelligence.prediction.services.prediction_analyzer import (
        PredictionAnalyzer,
    )

    from dairyos.intelligence.decision.services.decision_service import (
        DecisionService,
    )

    from dairyos.intelligence.decision.services.confidence_engine import (
        ConfidenceEngine,
    )


    assert PredictionService is not None
    assert PredictionAnalyzer is not None
    assert DecisionService is not None
    assert ConfidenceEngine is not None
