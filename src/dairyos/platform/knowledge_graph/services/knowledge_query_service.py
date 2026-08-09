from dairyos.platform.knowledge_graph.graph.query_engine import (
    KnowledgeQueryEngine,
)


from dairyos.platform.knowledge_graph.relationships.relationship_store import (
    RelationshipStore,
)



class KnowledgeQueryService:


    def __init__(self):

        self.store = RelationshipStore()

        self.engine = KnowledgeQueryEngine(

            self.store

        )



    def add_relationship(

        self,

        relationship,

    ):

        self.store.add(

            relationship

        )



    def find_connections(

        self,

        entity_id,

    ):

        return self.engine.connected_entities(

            entity_id

        )



    def find_related(

        self,

        entity_id,

        relation_type,

    ):

        return self.engine.related_to(

            entity_id,

            relation_type,

        )

