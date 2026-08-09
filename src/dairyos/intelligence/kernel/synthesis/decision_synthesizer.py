class DecisionSynthesizer:
    """
    Converts recommendations into structured intelligence decisions.
    """

    def synthesize(
        self,
        recommendations: list[dict],
    ) -> list[dict]:

        decisions = []

        for item in recommendations:

            if item["priority"] == "immediate":

                decisions.append(
                    {
                        "decision": item["recommendation"],
                        "priority": "immediate",
                        "reason": (
                            "Critical intelligence condition detected"
                        ),
                        "source": item["source"],
                        "category": item["category"],
                    }
                )

            elif item["priority"] == "high":

                decisions.append(
                    {
                        "decision": item["recommendation"],
                        "priority": "high",
                        "reason": (
                            "Elevated operational condition detected"
                        ),
                        "source": item["source"],
                        "category": item["category"],
                    }
                )

            else:

                decisions.append(
                    {
                        "decision": item["recommendation"],
                        "priority": "normal",
                        "reason": (
                            "Routine monitoring condition"
                        ),
                        "source": item["source"],
                        "category": item["category"],
                    }
                )

        return decisions
