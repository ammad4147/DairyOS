from dataclasses import dataclass



@dataclass
class TwinInsight:


    metric: str

    predicted_change: float

    explanation: str




class KnowledgeBridge:


    def enrich(

        self,

        metric,

        predicted_change,

        reasoning,

    ):


        return TwinInsight(

            metric=metric,

            predicted_change=predicted_change,

            explanation=reasoning,

        )

