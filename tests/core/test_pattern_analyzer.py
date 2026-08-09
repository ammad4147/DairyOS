from dairyos.intelligence.learning.services.pattern_analyzer import (
    PatternAnalyzer,
)

from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)


def test_pattern_analyzer_detects_critical_event_pattern():

    events = [
        IntelligenceEvent(
            event_type="signal_received",
            source="health",
            payload={
                "severity": "critical",
            },
        )
    ]


    analyzer = PatternAnalyzer()


    signals = analyzer.analyze(
        events
    )


    assert len(signals) == 1


    assert signals[0].category == (
        "operational_risk"
    )


    assert signals[0].confidence > 0


def test_pattern_analyzer_ignores_normal_events():

    events = [
        IntelligenceEvent(
            event_type="signal_received",
            source="production",
            payload={
                "severity": "normal",
            },
        )
    ]


    analyzer = PatternAnalyzer()


    signals = analyzer.analyze(
        events
    )


    assert len(signals) == 0
