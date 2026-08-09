from dairyos.intelligence.repository.intelligence_repository import (
    IntelligenceRepository,
)

from abc import ABC


def test_intelligence_repository_is_contract():

    assert issubclass(
        IntelligenceRepository,
        ABC,
    )


    assert hasattr(
        IntelligenceRepository,
        "save_signal",
    )


    assert hasattr(
        IntelligenceRepository,
        "save_decision",
    )


    assert hasattr(
        IntelligenceRepository,
        "save_outcome",
    )


    assert hasattr(
        IntelligenceRepository,
        "get_signals",
    )


    assert hasattr(
        IntelligenceRepository,
        "get_decisions",
    )


    assert hasattr(
        IntelligenceRepository,
        "get_outcomes",
    )
