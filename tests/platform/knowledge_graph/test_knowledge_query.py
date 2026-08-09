from dairyos.platform.knowledge_graph.services.knowledge_query_service import (
    KnowledgeQueryService,
)


from dairyos.platform.knowledge_graph.relationships.relationship import (
    Relationship,
)



def test_graph_connection_query():


    service = KnowledgeQueryService()



    relationship = Relationship(

        source_id="cow102",

        relation_type="produces",

        target_id="milk5501",

    )



    service.add_relationship(

        relationship

    )



    result = service.find_connections(

        "cow102"

    )



    assert len(result) == 1


    assert result[0]["target"] == "milk5501"



def test_relationship_filtering():


    service = KnowledgeQueryService()



    service.add_relationship(

        Relationship(

            source_id="cow102",

            relation_type="health",

            target_id="mastitis_event",

        )

    )



    result = service.find_related(

        "cow102",

        "health",

    )


    assert result[0] == "mastitis_event"

