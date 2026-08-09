class HerdKPIService:



    def utilization(

        self,

        total_animals,

        capacity

    ):


        if capacity == 0:

            return 0


        return round(

            (total_animals / capacity) * 100,

            2

        )



    def milking_ratio(

        self,

        milking,

        total

    ):


        if total == 0:

            return 0


        return round(

            (milking / total) * 100,

            2

        )
