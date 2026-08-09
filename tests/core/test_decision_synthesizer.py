from dairyos.intelligence.kernel.synthesis.decision_synthesizer import (
    DecisionSynthesizer,
)


def test_decision_synthesizer_creates_final_decision():

    recommendations = [
        {
            "priority": "immediate",
            "recommendation": "Immediate inspection required",
            "source": "health",
            "category": "animal_health",
        }
    ]


    synthesizer = DecisionSynthesizer()

    decisions = synthesizer.synthesize(
        recommendations
    )


    assert len(decisions) == 1

    assert (
        decisions[0]["decision"]
        ==
        "Immediate inspection required"
    )

    assert (
        decisions[0]["priority"]
        ==
        "immediate"
    )
