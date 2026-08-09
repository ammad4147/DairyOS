from dataclasses import dataclass


@dataclass
class OperationalScore:
    """
    Represents operational performance scoring.
    """

    total_tasks: int
    completed_tasks: int
    delayed_tasks: int
    critical_issues: int

    @property
    def completion_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0

        return (
            self.completed_tasks /
            self.total_tasks
        ) * 100

    @property
    def operational_health_score(self) -> float:
        score = self.completion_rate

        score -= self.delayed_tasks * 2
        score -= self.critical_issues * 5

        if score < 0:
            return 0.0

        return round(score, 2)
