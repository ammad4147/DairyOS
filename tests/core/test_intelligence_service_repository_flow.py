from dairyos.intelligence.services.intelligence_service import (
    IntelligenceService,
)

from dairyos.intelligence.repository.adapters.memory_repository import (
    InMemoryIntelligenceRepository,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)


def test_intelligence_service_persists_signal():

    repository = InMemoryIntelligenceRepository()


    service = IntelligenceService(
        repository=repository,
    )


    signal = IntelligenceSignal(
        source="health",
        category="animal_health",
        message="Critical temperature alert",
        severity="critical",
    )


    service.submit_signal(
        signal
    )


    stored_signals = repository.get_signals()


    assert len(
        stored_signals
    ) == 1


    assert (
        stored_signals[0].message
        ==
        "Critical temperature alert"
    )


def test_intelligence_service_processes_with_repository():

    repository = InMemoryIntelligenceRepository()


    service = IntelligenceService(
        repository=repository,
    )


    service.submit_signal(
        IntelligenceSignal(
            source="production",
            category="milk",
            message="Production variance detected",
            severity="normal",
        )
    )


    result = service.process()


    assert result is not None


    assert len(
        repository.get_signals()
    ) == 1
