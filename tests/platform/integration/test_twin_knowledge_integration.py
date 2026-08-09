from dairyos.platform.digital_twin.integration.knowledge_bridge import (
    KnowledgeBridge,
)


from dairyos.platform.knowledge_graph.integration.twin_adapter import (
    TwinKnowledgeAdapter,
)




def test_prediction_enrichment():


    bridge = KnowledgeBridge()



    insight = bridge.enrich(

        metric="milk",

        predicted_change=-8,

        reasoning="feed and health factors",

    )



    assert insight.metric == "milk"


    assert insight.predicted_change == -8


    assert (

        insight.explanation

        ==

        "feed and health factors"

    )




def test_context_creation():


    adapter = TwinKnowledgeAdapter()



    result = adapter.create_context(

        prediction="milk decline",

        knowledge="feed change",

    )



    assert result["prediction"] == "milk decline"


    assert result["knowledge"] == "feed change"

