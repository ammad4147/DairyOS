from dairyos.platform.knowledge_graph.relationships.relationship import (
    Relationship,
)


from dairyos.platform.knowledge_graph.relationships.relationship_store import (
    RelationshipStore,
)



class RelationshipService:


    def __init__(self):

        self.store = RelationshipStore()



    def connect(

        self,

        source_id,

        relation_type,

        target_id,

    ):


        relationship = Relationship(

            source_id=source_id,

            relation_type=relation_type,

            target_id=target_id,

        )


        return self.store.add(

            relationship

        )



    def connections(

        self,

        entity_id,

    ):

        return self.store.find_by_source(

            entity_id

        )

