from ..models.condition_reference import ConditionReference



class ClinicalKnowledgeService:



    def __init__(self):

        self.conditions = [

            ConditionReference(

                "Mastitis",

                "Udder Health",

                [

                    "milk_drop",

                    "abnormal_milk",

                    "udder_change"

                ],

                [

                    "Udder examination",

                    "Milk quality check",

                    "Temperature check"

                ],

                "DairyOS Clinical Knowledge Base"

            ),

            ConditionReference(

                "Metabolic Disorder",

                "Metabolic",

                [

                    "feed_drop",

                    "activity_drop",

                    "milk_drop"

                ],

                [

                    "Body condition review",

                    "Feed assessment",

                    "Veterinary examination"

                ],

                "DairyOS Clinical Knowledge Base"

            )

        ]



    def find_by_indicator(

        self,

        indicator

    ):

        results = []


        for condition in self.conditions:

            if indicator in condition.related_indicators:

                results.append(condition)


        return results
