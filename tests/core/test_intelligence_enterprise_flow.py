from dairyos.intelligence.api.intelligence_api import (
    IntelligenceAPI,
)

from dairyos.intelligence.repository.adapters.memory_repository import (
    InMemoryIntelligenceRepository,
)

from dairyos.intelligence.services.intelligence_service import (
    IntelligenceService,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)


def test_complete_enterprise_intelligence_flow():

    repository = InMemoryIntelligenceRepository()


    service = IntelligenceService(
        repository=repository,
    )


    api = IntelligenceAPI(
        service=service,
    )


    signal = IntelligenceSignal(
        source="health",
        category="animal_health",
        message="Critical temperature detected",
        severity="critical",
    )


    api.submit_signal(
        signal
    )


    result = api.process()


    assert isinstance(
        result,
        dict,
    )


    assert len(
        repository.get_signals()
    ) == 1


    assert (
        repository.get_signals()[0].severity
        ==
        "critical"
    )
