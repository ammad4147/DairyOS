from dairyos.intelligence.kernel.context.intelligence_context import (
    IntelligenceContext,
)


class SituationAssessment:
    """
    Deterministic operational intelligence assessment.

    Converts current intelligence context into
    a structured situation view.

    Future extensions:
    - predictive analysis
    - machine learning models
    - autonomous reasoning
    """

    def assess(
        self,
        context: IntelligenceContext,
    ):

        highest_severity = "normal"

        for signal in context.signals:

            if signal.severity == "critical":

                highest_severity = "critical"
                break

            if signal.severity == "high":

                highest_severity = "high"


        unresolved_outcomes = 0

        for outcome in context.outcomes:

            if outcome.status != "completed":

                unresolved_outcomes += 1


        pressure = "normal"

        if highest_severity in (
            "high",
            "critical",
        ):

            pressure = "elevated"


        if unresolved_outcomes > 0:

            pressure = "attention_required"


        return {
            "signal_count": len(context.signals),
            "decision_count": len(context.decisions),
            "outcome_count": len(context.outcomes),
            "highest_severity": highest_severity,
            "unresolved_outcomes": unresolved_outcomes,
            "operational_pressure": pressure,
        }
