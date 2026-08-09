from dairyos.platform.knowledge_graph.graph.knowledge_graph import (
    KnowledgeGraph,
)



class KnowledgeService:


    def __init__(self):

        self.graph = KnowledgeGraph()



    def register_entity(

        self,

        entity_id,

        entity,

    ):

        self.graph.add_entity(

            entity_id,

            entity,

        )


        return entity

