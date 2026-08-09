from ..models.milk_quality import MilkQuality



class MilkQualityService:



    def evaluate(

        self,

        batch_id,

        volume_litres,

        fat_percentage,

        protein_percentage

    ):


        if fat_percentage >= 3.5 and protein_percentage >= 3.0:

            quality_status = "GOOD"

            quality_grade = "PREMIUM"


        elif fat_percentage >= 3.2:

            quality_status = "ACCEPTABLE"

            quality_grade = "STANDARD"


        else:

            quality_status = "ATTENTION"

            quality_grade = "LOW"



        return MilkQuality(

            batch_id,

            volume_litres,

            fat_percentage,

            protein_percentage,

            quality_status,

            quality_grade

        )
