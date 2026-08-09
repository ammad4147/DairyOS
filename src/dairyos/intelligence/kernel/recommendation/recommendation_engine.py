class RecommendationEngine:
    """
    Converts prioritized intelligence situations
    into operational recommendations.
    """

    def generate(
        self,
        priorities: list[dict],
    ) -> list[dict]:

        recommendations = []

        for item in priorities:

            if item["priority"] == "immediate":

                recommendations.append(
                    {
                        "priority": "immediate",
                        "recommendation": (
                            "Immediate inspection required"
                        ),
                        "source": item["source"],
                        "category": item["category"],
                    }
                )

            elif item["priority"] == "high":

                recommendations.append(
                    {
                        "priority": "high",
                        "recommendation": (
                            "Review operational conditions"
                        ),
                        "source": item["source"],
                        "category": item["category"],
                    }
                )

            else:

                recommendations.append(
                    {
                        "priority": "normal",
                        "recommendation": (
                            "Continue monitoring"
                        ),
                        "source": item["source"],
                        "category": item["category"],
                    }
                )

        return recommendations
