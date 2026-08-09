from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.kernel.services.domain_integration import (
    IntelligenceDomainIntegration,
)


def test_domain_integration_processes_signal():

    integration = IntelligenceDomainIntegration()

    signal = IntelligenceSignal(
        source="herd",
        category="health",
        message="Animal requires monitoring",
        severity="normal",
    )

    decision = integration.process_signal(signal)

    assert decision.action == "Monitor situation"
    assert decision.rationale == "Animal requires monitoring"