from typing import Dict, List

from dairyos.operations.outcomes.models.operational_outcome import (
    OperationalOutcome,
)

from dairyos.operations.learning.models.learning_signal import (
    LearningSignal,
)

from dairyos.operations.learning.services.learning_service import (
    LearningService,
)

from dairyos.operations.learning.services.pattern_detection_service import (
    PatternDetectionService,
)

from dairyos.operations.learning.services.improvement_service import (
    ImprovementService,
)

from dairyos.operations.memory.services.pattern_learning_service import (
    PatternLearningService,
)

from dairyos.operations.memory.services.memory_service import (
    MemoryService,
)


class OperationalLearningBridge:
    """
    Integrates completed operational outcomes
    into the operational learning loop.

    Converts execution experience into:
    - learning signals
    - operational patterns
    - improvement opportunities
    - reusable operational memory
    """

    def __init__(
        self,
        learning_service: LearningService | None = None,
        pattern_detection_service: PatternDetectionService | None = None,
        improvement_service: ImprovementService | None = None,
        pattern_learning_service: PatternLearningService | None = None,
        memory_service: MemoryService | None = None,
    ):

        self.learning_service = (
            learning_service
            if learning_service is not None
            else LearningService()
        )

        self.pattern_detection_service = (
            pattern_detection_service
            if pattern_detection_service is not None
            else PatternDetectionService()
        )

        self.improvement_service = (
            improvement_service
            if improvement_service is not None
            else ImprovementService()
        )

        self.pattern_learning_service = (
            pattern_learning_service
            if pattern_learning_service is not None
            else PatternLearningService()
        )

        self.memory_service = (
            memory_service
            if memory_service is not None
            else MemoryService()
        )



    def process_outcome(
        self,
        outcome: OperationalOutcome,
    ) -> Dict:

        signal = LearningSignal(

            signal_id=(
                f"SIG-{outcome.outcome_id}"
            ),

            category=(
                outcome.rating.rating
            ),

            description=(
                outcome.result
            ),

            impact_level=(
                outcome.rating.rating
            ),

            created_at=(
                outcome.created_at
            ),

        )


        self.learning_service.record_signal(
            signal
        )


        signals = (
            self.learning_service
            .get_signals()
        )


        patterns = (
            self.pattern_detection_service
            .detect_patterns(
                signals
            )
        )


        opportunities = (
            self.improvement_service
            .create_opportunities(
                patterns
            )
        )


        memories = []


        for pattern in patterns:

            knowledge_pattern = (
                self.pattern_learning_service
                .create_pattern(
                    category=pattern.category,
                    situation=(
                        pattern.name
                    ),
                    response=(
                        "Apply improved operational response"
                    ),
                    confidence=(
                        min(
                            pattern.occurrence_count
                            / 10,
                            1.0,
                        )
                    ),
                )
            )


            memory = (
                self.memory_service
                .store(
                    knowledge_pattern
                )
            )


            memories.append(
                memory
            )


        return {

            "learning_signal": signal,

            "patterns": patterns,

            "improvement_opportunities": (
                opportunities
            ),

            "operational_memories": (
                memories
            ),

        }
