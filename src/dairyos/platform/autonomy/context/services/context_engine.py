from dairyos.platform.autonomy.context.models.decision_context import (
    DecisionContext,
)



class ContextEngine:
    """
    Builds decision-ready operational context.
    """



    def build(

        self,

        problem,

        evidence,

        impact,

        confidence,

    ):


        return DecisionContext(

            problem=problem,

            evidence=evidence,

            impact=impact,

            confidence=confidence,

        )

