class GraphTraversal:


    def __init__(self, store):

        self.store = store



    def connections(

        self,

        entity_id,

    ):

        return self.store.find_by_source(

            entity_id

        )

