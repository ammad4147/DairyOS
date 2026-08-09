from dairyos.operations.workforce_intelligence.repositories.execution_metric_repository import (
    ExecutionMetricRepository,
)

from dairyos.operations.workforce_intelligence.repositories.workforce_accountability_repository import (
    WorkforceAccountabilityRepository,
)

from dairyos.operations.workforce_intelligence.repositories.workforce_ownership_repository import (
    WorkforceOwnershipRepository,
)

from dairyos.operations.workforce_intelligence.services.workforce_execution_intelligence_service import (
    WorkforceExecutionIntelligenceService,
)

from dairyos.operations.workforce_intelligence.services.summary.workforce_performance_summary_service import (
    WorkforcePerformanceSummaryService,
)

from dairyos.operations.workforce_intelligence.services.summary.workforce_reliability_summary_service import (
    WorkforceReliabilitySummaryService,
)

from dairyos.operations.workforce_intelligence.services.workforce_accountability_service import (
    WorkforceAccountabilityService,
)

from dairyos.operations.workforce_intelligence.services.summary.workforce_accountability_summary_service import (
    WorkforceAccountabilitySummaryService,
)

from dairyos.operations.workforce_intelligence.services.workforce_ownership_service import (
    WorkforceOwnershipService,
)

from dairyos.operations.workforce_intelligence.services.summary.workforce_ownership_summary_service import (
    WorkforceOwnershipSummaryService,
)

from dairyos.operations.workforce_intelligence.services.workforce_command_service import (
    WorkforceCommandService,
)



def main():

    print("=" * 60)

    print(
        "SPRINT 064 WORKFORCE COMMAND INTELLIGENCE VERIFICATION"
    )

    print("=" * 60)



    execution_repository = (
        ExecutionMetricRepository()
    )


    accountability_repository = (
        WorkforceAccountabilityRepository()
    )


    ownership_repository = (
        WorkforceOwnershipRepository()
    )



    execution_service = (
        WorkforceExecutionIntelligenceService(
            execution_repository
        )
    )


    performance_service = (
        WorkforcePerformanceSummaryService(
            execution_repository
        )
    )


    reliability_service = (
        WorkforceReliabilitySummaryService(
            execution_repository
        )
    )


    accountability_service = (
        WorkforceAccountabilityService(
            execution_repository,
            accountability_repository,
        )
    )


    accountability_summary_service = (
        WorkforceAccountabilitySummaryService(
            accountability_service
        )
    )


    ownership_service = (
        WorkforceOwnershipService(
            execution_repository,
            ownership_repository,
        )
    )


    ownership_summary_service = (
        WorkforceOwnershipSummaryService(
            ownership_service
        )
    )



    command_service = (
        WorkforceCommandService(
            execution_service,
            performance_service,
            reliability_service,
            accountability_summary_service,
            ownership_summary_service,
        )
    )



    snapshot = (
        command_service.generate_snapshot()
    )



    print()

    print(
        "Workforce Command Snapshot:"
    )

    print(
        snapshot
    )



    assert snapshot.execution_health == "GREEN"

    assert snapshot.performance_status == "GREEN"

    assert snapshot.reliability_status == "HIGH"

    assert snapshot.accountability_status == "HIGH"

    assert snapshot.ownership_status == "HIGH"

    assert snapshot.management_attention_required is False

    assert snapshot.priority_level == "NORMAL"



    print()

    print(
        "SPRINT 064 WORKFORCE COMMAND INTELLIGENCE READY"
    )



if __name__ == "__main__":

    main()
