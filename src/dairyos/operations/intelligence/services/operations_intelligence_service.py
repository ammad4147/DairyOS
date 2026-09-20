
from ..models.operational_score import OperationalScore
from ..models.operational_signal import OperationalSignal


class OperationsIntelligenceService:
    """
    Converts operational activity into intelligence.
    """

    def __init__(self):
        self.signals: list[OperationalSignal] = []

    def register_signal(
        self,
        signal: OperationalSignal,
    ) -> OperationalSignal:

        self.signals.append(signal)

        return signal


    def active_signals(self) -> list[OperationalSignal]:

        return [
            signal
            for signal in self.signals
            if not signal.resolved
        ]


    def calculate_score(
        self,
        total_tasks: int,
        completed_tasks: int,
        delayed_tasks: int,
        critical_issues: int,
    ) -> OperationalScore:

        return OperationalScore(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            delayed_tasks=delayed_tasks,
            critical_issues=critical_issues,
        )
