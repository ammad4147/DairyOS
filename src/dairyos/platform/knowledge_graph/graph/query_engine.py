class KnowledgeQueryEngine:


    def __init__(

        self,

        relationship_store,

    ):

        self.relationship_store = relationship_store



    def connected_entities(

        self,

        entity_id,

    ):


        relationships = (

            self.relationship_store

            .find_by_source(entity_id)

        )


        return [

            {

                "relation":

                    r.relation_type,

                "target":

                    r.target_id,

            }

            for r in relationships

        ]



    def related_to(

        self,

        entity_id,

        relation_type,

    ):


        relationships = (

            self.relationship_store

            .find_by_source(entity_id)

        )


        return [

            r.target_id

            for r in relationships

            if r.relation_type == relation_type

        ]

