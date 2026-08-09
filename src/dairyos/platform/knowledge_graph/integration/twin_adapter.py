class TwinKnowledgeAdapter:


    def create_context(

        self,

        prediction,

        knowledge,

    ):


        return {

            "prediction":

                prediction,

            "knowledge":

                knowledge,

        }

