from dairyos.platform.knowledge_graph.reasoning.reasoning_result import (
    ReasoningResult,
)



class ReasoningEngine:


    def analyze(

        self,

        observation,

        evidence,

    ):


        confidence = 0



        for item in evidence:

            confidence += item.confidence



        if evidence:

            confidence = confidence / len(evidence)



        conclusion = (

            "Potential causes identified"

        )



        return ReasoningResult(

            observation=observation,

            conclusion=conclusion,

            confidence=confidence,

            evidence_count=len(evidence),

        )

