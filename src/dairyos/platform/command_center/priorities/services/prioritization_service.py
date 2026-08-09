from dairyos.platform.command_center.priorities.models.priority_score import (
    PriorityScore,
)



class PrioritizationService:
    """
    Converts operational signals into ranked priorities.
    """



    def calculate(
        self,
        severity,
        impact,
        urgency,
    ):


        score = 0


        if severity == "critical":

            score += 40

        elif severity == "high":

            score += 30

        elif severity == "medium":

            score += 20


        if impact == "high":

            score += 30

        elif impact == "medium":

            score += 20


        if urgency == "immediate":

            score += 30

        elif urgency == "today":

            score += 20


        return PriorityScore(

            score=score,

            severity=severity,

            impact=impact,

            urgency=urgency,

        )

