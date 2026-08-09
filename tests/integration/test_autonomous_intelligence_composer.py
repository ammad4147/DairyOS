from dairyos.intelligence.integration.autonomous_intelligence_composer import (
    AutonomousIntelligenceComposer,
)


def test_autonomous_intelligence_composer_creation():

    composer = AutonomousIntelligenceComposer()

    assert composer is not None


def test_autonomous_intelligence_composer_loop_creation():

    composer = AutonomousIntelligenceComposer()

    loop = composer.get_loop()

    assert loop is not None
