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


def test_intelligence_api_submits_signal():

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
        message="API health alert",
        severity="critical",
    )


    result = api.submit_signal(
        signal
    )


    assert result == signal


    assert len(
        repository.get_signals()
    ) == 1


def test_intelligence_api_processes_request():

    api = IntelligenceAPI()


    result = api.process()


    assert isinstance(
        result,
        dict,
    )
