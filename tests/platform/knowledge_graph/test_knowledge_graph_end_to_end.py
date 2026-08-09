from dairyos.platform.knowledge_graph.services.knowledge_service import (
    KnowledgeService,
)


from dairyos.platform.knowledge_graph.services.relationship_service import (
    RelationshipService,
)


from dairyos.platform.knowledge_graph.services.reasoning_service import (
    ReasoningService,
)


from dairyos.platform.knowledge_graph.reasoning.evidence import (
    Evidence,
)


from dairyos.platform.knowledge_graph.entities.animal_entity import (
    AnimalEntity,
)




def test_complete_knowledge_flow():


    knowledge = KnowledgeService()



    animal = AnimalEntity(

        animal_id="cow102",

        name="Cow 102",

        breed="Holstein",

        status="lactating",

    )



    knowledge.register_entity(

        "cow102",

        animal,

    )



    relationships = RelationshipService()



    relationships.connect(

        "cow102",

        "produces",

        "milk_record_001",

    )



    reasoning = ReasoningService()



    result = reasoning.reason(

        "milk decline",

        [

            Evidence(

                source="feed_change",

                relation="affects",

                confidence=0.8,

            )

        ],

    )



    assert knowledge.graph.get_entity(

        "cow102"

    ) == animal



    assert len(

        relationships.connections("cow102")

    ) == 1



    assert result.confidence == 0.8

