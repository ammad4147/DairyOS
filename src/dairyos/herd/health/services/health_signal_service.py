from datetime import datetime

from ..models.health_signal import HealthSignal



class HealthSignalService:



    def detect_milk_drop(

        self,

        animal_id,

        current_yield,

        normal_yield,

        source="Milking System"

    ):

        deviation = (

            (normal_yield - current_yield)

            /

            normal_yield

        ) * 100



        severity = "NORMAL"


        if deviation >= 20:

            severity = "HIGH"

        elif deviation >= 10:

            severity = "MEDIUM"



        return HealthSignal(

            animal_id,

            "MILK_YIELD_DROP",

            str(current_yield),

            str(normal_yield),

            f"{round(deviation,2)}%",

            severity,

            source,

            datetime.now()

        )



    def detect_feed_drop(

        self,

        animal_id,

        current_intake,

        normal_intake,

        source="Feed System"

    ):

        deviation = (

            (normal_intake - current_intake)

            /

            normal_intake

        ) * 100



        severity = "NORMAL"


        if deviation >= 20:

            severity = "HIGH"

        elif deviation >= 10:

            severity = "MEDIUM"



        return HealthSignal(

            animal_id,

            "FEED_INTAKE_DROP",

            str(current_intake),

            str(normal_intake),

            f"{round(deviation,2)}%",

            severity,

            source,

            datetime.now()

        )
