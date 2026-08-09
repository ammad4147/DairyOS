from dairyos.intelligence.integration.decision_governance import (
    GovernanceDecision,
)


class DecisionGovernanceService:
    """
    Controls whether autonomous decisions
    may proceed to command execution.

    Initial deterministic policy:

    confidence >= 0.8
        approved

    confidence < 0.8
        requires_review
    """


    def evaluate(
        self,
        decision,
    ):

        if not decision:

            return GovernanceDecision(
                status="rejected",
                reason="No decision available",
                approved=False,
            )


        confidence = self._extract_confidence(
            decision
        )


        if confidence >= 0.8:

            return GovernanceDecision(
                status="approved",
                reason="Decision confidence meets autonomous execution threshold",
                approved=True,
            )


        return GovernanceDecision(
            status="requires_review",
            reason="Decision requires human review",
            approved=False,
        )



    def _extract_confidence(
        self,
        decision,
    ):

        if isinstance(
            decision,
            list,
        ):

            if len(decision) == 0:

                return 0.0


            item = decision[0]


            if isinstance(
                item,
                dict,
            ):

                confidence = item.get(
                    "confidence"
                )

                if confidence:

                    return (
                        confidence.confidence_score
                        if hasattr(
                            confidence,
                            "confidence_score",
                        )
                        else 0.0
                    )


        return 0.0
