from dairyos.platform.knowledge_graph.services.reasoning_service import (
    ReasoningService,
)


from dairyos.platform.knowledge_graph.reasoning.evidence import (
    Evidence,
)



def test_reasoning_generates_explanation():


    service = ReasoningService()



    result = service.reason(

        observation="milk decline",

        evidence=[

            Evidence(

                source="feed_change",

                relation="affects",

                confidence=0.8,

            ),

            Evidence(

                source="health_event",

                relation="correlated",

                confidence=0.6,

            ),

        ],

    )



    assert result.observation == "milk decline"


    assert result.evidence_count == 2


    assert result.confidence == 0.7

