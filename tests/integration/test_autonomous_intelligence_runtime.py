from types import SimpleNamespace

from dairyos.intelligence.integration.autonomous_intelligence_composer import (
    AutonomousIntelligenceComposer,
)


def test_autonomous_intelligence_runtime_execution():

    composer = AutonomousIntelligenceComposer()

    signal = SimpleNamespace(
        category="operational_risk",
        confidence=0.85,
    )

    result = composer.run(
        [
            signal,
        ]
    )

    assert result is not None

    assert "prediction" in result

    assert "runtime" in result

    assert result["runtime"]["status"] == "completed"

    assert (
        "prediction"
        in result["runtime"]["stages"]
    )

    assert (
        "learning"
        in result["runtime"]["stages"]
    )
