from ..models.operational_health_snapshot import (
    OperationalHealthSnapshot,
)


class OperationsHealthService:
    """
    Aggregates operational modules into a single health snapshot.
    """


    def generate_snapshot(
        self,
        operational_score: float = 100.0,
        active_decisions: int = 0,
        pending_actions: int = 0,
        tracked_outcomes: int = 0,
        learning_signals: int = 0,
    ) -> OperationalHealthSnapshot:

        if pending_actions > 5:
            status = "AMBER"
            attention = True

        elif active_decisions > 10:
            status = "AMBER"
            attention = True

        else:
            status = "GREEN"
            attention = False


        return OperationalHealthSnapshot(
            health_status=status,
            operational_score=operational_score,
            active_decisions=active_decisions,
            pending_actions=pending_actions,
            tracked_outcomes=tracked_outcomes,
            learning_signals=learning_signals,
            owner_attention_required=attention,
        )
