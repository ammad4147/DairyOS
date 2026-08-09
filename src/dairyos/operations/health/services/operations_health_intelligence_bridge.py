from dairyos.operations.intelligence.services.operations_intelligence_service import (
    OperationsIntelligenceService,
)

from dairyos.operations.health.models.operational_health_snapshot import (
    OperationalHealthSnapshot,
)


class OperationsHealthIntelligenceBridge:
    """
    Bridges operational intelligence into health monitoring.
    """


    def __init__(self):

        self.intelligence_service = (
            OperationsIntelligenceService()
        )


    def generate_snapshot(
        self,
        total_tasks: int = 0,
        completed_tasks: int = 0,
        delayed_tasks: int = 0,
        critical_issues: int = 0,
    ):

        score = (
            self.intelligence_service
            .calculate_score(
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                delayed_tasks=delayed_tasks,
                critical_issues=critical_issues,
            )
        )


        operational_score = (
            score.operational_health_score
        )


        if operational_score >= 80:

            status = "GREEN"

            attention = False


        elif operational_score >= 50:

            status = "AMBER"

            attention = True


        else:

            status = "RED"

            attention = True



        return OperationalHealthSnapshot(

            health_status=status,

            operational_score=operational_score,

            active_decisions=critical_issues,

            pending_actions=delayed_tasks,

            tracked_outcomes=completed_tasks,

            learning_signals=0,

            owner_attention_required=attention,

        )
