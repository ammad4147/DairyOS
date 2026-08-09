from dairyos.intelligence.kernel.context.intelligence_context import IntelligenceContext


class DecisionPrioritizer:
    """
    Ranks intelligence situations according to operational urgency.
    """

    def prioritize(
        self,
        context: IntelligenceContext,
    ) -> list[dict]:

        priorities = []

        for signal in context.signals:

            if signal.severity == "critical":
                priorities.append(
                    {
                        "priority": "immediate",
                        "score": 100,
                        "source": signal.source,
                        "category": signal.category,
                        "message": signal.message,
                    }
                )

            elif signal.severity == "warning":
                priorities.append(
                    {
                        "priority": "high",
                        "score": 75,
                        "source": signal.source,
                        "category": signal.category,
                        "message": signal.message,
                    }
                )

            else:
                priorities.append(
                    {
                        "priority": "normal",
                        "score": 50,
                        "source": signal.source,
                        "category": signal.category,
                        "message": signal.message,
                    }
                )

        return sorted(
            priorities,
            key=lambda item: item["score"],
            reverse=True,
        )
