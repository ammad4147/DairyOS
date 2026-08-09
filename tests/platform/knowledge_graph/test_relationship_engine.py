from dairyos.platform.knowledge_graph.services.relationship_service import (
    RelationshipService,
)



def test_entity_relationship_creation():


    service = RelationshipService()



    relationship = service.connect(

        source_id="cow102",

        relation_type="produces",

        target_id="milk5501",

    )



    assert relationship.source_id == "cow102"


    connections = service.connections(

        "cow102"

    )


    assert len(connections) == 1


    assert connections[0].target_id == "milk5501"

