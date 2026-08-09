from ..models.clinical_completeness import ClinicalCompleteness



class ClinicalCompletenessService:



    REQUIRED_ITEMS = [

        "Observation",

        "History",

        "Examination",

        "Differential Assessment",

        "Diagnostic Plan"

    ]



    def review(

        self,

        animal_id,

        completed_items

    ):

        missing = [

            item

            for item in self.REQUIRED_ITEMS

            if item not in completed_items

        ]


        return ClinicalCompleteness(

            animal_id,

            completed_items,

            missing,

            len(missing) == 0

        )
