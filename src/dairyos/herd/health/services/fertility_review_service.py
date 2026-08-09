class FertilityReviewService:



    def review(

        self,

        insemination_records

    ):

        failures = [

            record

            for record in insemination_records

            if record.pregnancy_result != "PREGNANT"

        ]


        attempts = len(insemination_records)


        return {

            "attempts": attempts,

            "failures": len(failures),

            "review_required":

                attempts >= 3 and len(failures) >= 3

        }
