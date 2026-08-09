class KnowledgeGraph:


    def __init__(self):

        self.entities = {}

        self.relationships = []



    def add_entity(

        self,

        entity_id,

        entity,

    ):

        self.entities[entity_id] = entity



    def add_relationship(

        self,

        relationship,

    ):

        self.relationships.append(

            relationship

        )



    def get_entity(

        self,

        entity_id,

    ):

        return self.entities.get(

            entity_id

        )

