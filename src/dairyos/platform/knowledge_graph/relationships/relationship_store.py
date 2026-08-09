from dairyos.platform.knowledge_graph.relationships.relationship import (
    Relationship,
)



class RelationshipStore:


    def __init__(self):

        self.relationships = []



    def add(

        self,

        relationship: Relationship,

    ):

        self.relationships.append(

            relationship

        )


        return relationship



    def find_by_source(

        self,

        source_id,

    ):

        return [

            r

            for r in self.relationships

            if r.source_id == source_id

        ]



    def find_by_target(

        self,

        target_id,

    ):

        return [

            r

            for r in self.relationships

            if r.target_id == target_id

        ]

