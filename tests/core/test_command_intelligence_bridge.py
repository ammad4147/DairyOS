from dairyos.intelligence.command.integration.command_intelligence_bridge import (
    CommandIntelligenceBridge,
)

from dairyos.intelligence.command.services.command_orchestrator import (
    CommandOrchestrator,
)

from dairyos.intelligence.command.services.situation_analysis_service import (
    SituationAnalysisService,
)

from dairyos.intelligence.command.services.recommendation_service import (
    RecommendationService,
)

from dairyos.intelligence.command.services.command_execution_service import (
    CommandExecutionService,
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



def test_command_intelligence_bridge():

    orchestrator = CommandOrchestrator(
        SituationAnalysisService(
            MemorySituationRepository()
        ),
        RecommendationService(
            MemoryRecommendationRepository()
        ),
        CommandExecutionService(
            MemoryActionRepository()
        ),
    )

    bridge = CommandIntelligenceBridge(
        orchestrator
    )

    assert bridge is not None
