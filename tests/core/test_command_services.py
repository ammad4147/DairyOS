from dairyos.intelligence.command.services.command_execution_service import (
    CommandExecutionService,
)

from dairyos.intelligence.command.services.command_orchestrator import (
    CommandOrchestrator,
)

from dairyos.intelligence.command.services.recommendation_service import (
    RecommendationService,
)

from dairyos.intelligence.command.services.situation_analysis_service import (
    SituationAnalysisService,
)

from dairyos.intelligence.command.repository.adapters.memory_action_repository import (
    MemoryActionRepository,
)

from dairyos.intelligence.command.repository.adapters.memory_recommendation_repository import (
    MemoryRecommendationRepository,
)

from dairyos.intelligence.command.repository.adapters.memory_situation_repository import (
    MemorySituationRepository,
)



def test_command_execution_service_creation():

    repository = MemoryActionRepository()

    service = CommandExecutionService(
        repository
    )

    assert service is not None



def test_command_orchestrator_creation():

    situation_service = SituationAnalysisService(
        MemorySituationRepository()
    )

    recommendation_service = RecommendationService(
        MemoryRecommendationRepository()
    )

    execution_service = CommandExecutionService(
        MemoryActionRepository()
    )

    orchestrator = CommandOrchestrator(
        situation_service,
        recommendation_service,
        execution_service,
    )

    assert orchestrator is not None



def test_recommendation_service_creation():

    service = RecommendationService(
        MemoryRecommendationRepository()
    )

    assert service is not None



def test_situation_analysis_service_creation():

    service = SituationAnalysisService(
        MemorySituationRepository()
    )

    assert service is not None
