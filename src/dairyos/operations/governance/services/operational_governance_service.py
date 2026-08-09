from typing import Any, Dict, List


from dairyos.operations.command_center.services.execution_accountability_query_service import (
    ExecutionAccountabilityQueryService,
)

from dairyos.operations.resolution.services.resolution_management_service import (
    ResolutionManagementService,
)

from dairyos.operations.resolution.services.resolution_verification_service import (
    ResolutionVerificationService,
)

from dairyos.operations.outcomes.services.outcome_analysis_service import (
    OutcomeAnalysisService,
)

from dairyos.operations.effectiveness.services.effectiveness_analysis_service import (
    EffectivenessAnalysisService,
)

from dairyos.operations.closure_intelligence.services.closure_intelligence_service import (
    ClosureIntelligenceService,
)



class OperationalGovernanceService:
    """
    Operational governance orchestration boundary.

    Coordinates operational accountability,
    corrective resolution,
    outcome learning,
    effectiveness evaluation,
    and closure intelligence.

    This service:
    - does not own operational state
    - does not mutate farm state
    - does not create automatic workflows
    - does not replace domain services

    Application orchestration only.
    """


    def __init__(
        self,
        accountability_service: ExecutionAccountabilityQueryService | None = None,
        resolution_management_service: ResolutionManagementService | None = None,
        resolution_verification_service: ResolutionVerificationService | None = None,
        outcome_analysis_service: OutcomeAnalysisService | None = None,
        effectiveness_analysis_service: EffectivenessAnalysisService | None = None,
        closure_intelligence_service: ClosureIntelligenceService | None = None,
    ):


        self.accountability_service = (
            accountability_service
            if accountability_service is not None
            else ExecutionAccountabilityQueryService()
        )


        self.resolution_management_service = (
            resolution_management_service
            if resolution_management_service is not None
            else ResolutionManagementService()
        )


        self.resolution_verification_service = (
            resolution_verification_service
            if resolution_verification_service is not None
            else ResolutionVerificationService()
        )


        self.outcome_analysis_service = (
            outcome_analysis_service
            if outcome_analysis_service is not None
            else OutcomeAnalysisService()
        )


        self.effectiveness_analysis_service = (
            effectiveness_analysis_service
            if effectiveness_analysis_service is not None
            else EffectivenessAnalysisService()
        )


        self.closure_intelligence_service = (
            closure_intelligence_service
            if closure_intelligence_service is not None
            else ClosureIntelligenceService()
        )



    def build_governance_view(
        self,
        accountability_records: List | None = None,
        outcomes: List | None = None,
        effectiveness=None,
    ) -> Dict[str, Any]:
        """
        Creates governance projection.

        Read-side coordination only.
        """


        accountability = (
            self.accountability_service
            .build_projection(
                accountability_records
            )
        )


        successful_outcomes = (
            self.outcome_analysis_service
            .successful_outcomes(
                outcomes or []
            )
        )


        failed_outcomes = (
            self.outcome_analysis_service
            .failed_outcomes(
                outcomes or []
            )
        )


        effectiveness_status = None


        if effectiveness is not None:

            effectiveness_status = (
                self.effectiveness_analysis_service
                .evaluate(
                    effectiveness
                )
            )


        return {

            "accountability":
                accountability,

            "successful_outcome_count":
                len(successful_outcomes),

            "failed_outcome_count":
                len(failed_outcomes),

            "effectiveness_status":
                effectiveness_status,

            "governance_ready":
                True,

        }



    def assess_closure(
        self,
        execution_id: str,
        task_name: str,
        completed: bool,
        performance_score: float,
    ):

        return (
            self.closure_intelligence_service
            .assess(
                execution_id=execution_id,
                task_name=task_name,
                completed=completed,
                performance_score=performance_score,
            )
        )
