from ..models.advisory import Advisory



class AdvisoryService:



    def generate(

        self,

        category,

        situation,

        knowledge=None

    ):


        if knowledge:

            confidence = knowledge.confidence

            supporting = knowledge.observation

        else:

            confidence = 50

            supporting = "No historical knowledge available"



        actions = {

            "HERD STRATEGY":

                "Begin replacement acquisition planning",

            "HEALTH":

                "Review animal health intervention",

            "REPRODUCTION":

                "Review breeding performance",

            "PRODUCTION":

                "Review production performance",

            "FINANCE":

                "Review financial indicators"

        }



        action = actions.get(

            category,

            "Review farm condition"

        )



        return Advisory(

            category,

            situation,

            supporting,

            confidence,

            action

        )



    def compare_confidence(

        self,

        advisory_a,

        advisory_b

    ):


        return (

            advisory_a

            if advisory_a.confidence >= advisory_b.confidence

            else advisory_b

        )
