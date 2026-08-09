from dairyos.intelligence.kernel.models.intelligence_signal import IntelligenceSignal
from dairyos.intelligence.kernel.services.intelligence_kernel import IntelligenceKernel


def test_intelligence_kernel_creates_decision():

    signal = IntelligenceSignal(
        source="operations",
        category="workflow",
        message="Morning feeding record missing",
        severity="normal",
    )

    kernel = IntelligenceKernel()

    decision = kernel.evaluate(signal)

    assert decision.action == "Monitor situation"
    assert decision.priority == "normal"



def test_intelligence_kernel_handles_critical_signal():

    signal = IntelligenceSignal(
        source="health",
        category="animal_health",
        message="Possible disease outbreak detected",
        severity="critical",
    )

    kernel = IntelligenceKernel()

    decision = kernel.evaluate(signal)

    assert decision.priority == "high"

