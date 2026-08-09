from dairyos.platform.knowledge_graph.reasoning.reasoning_engine import (
    ReasoningEngine,
)



class ReasoningService:


    def __init__(self):

        self.engine = ReasoningEngine()



    def reason(

        self,

        observation,

        evidence,

    ):


        return self.engine.analyze(

            observation,

            evidence,

        )

