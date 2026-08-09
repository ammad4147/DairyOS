class MilkAnomalyService:


    def detect_drop(
        self,
        animal_id,
        historical_average,
        current_yield
    ):


        if historical_average <= 0:

            return None



        drop = (

            (
                historical_average
                -
                current_yield
            )
            /
            historical_average

        ) * 100



        if drop < 30:

            return None



        severity = "MEDIUM"


        if drop >= 40:

            severity = "HIGH"



        return {

            "animal_id": animal_id,

            "anomaly": "MILK_DROP",

            "deviation_percentage": round(
                drop,
                2
            ),

            "severity": severity,

        }
