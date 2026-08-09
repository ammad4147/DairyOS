class MilkAlertService:


    def missing_entry_alert(
        self,
        recorded_animals,
        expected_animals
    ):

        missing = (
            expected_animals
            -
            recorded_animals
        )


        if missing <= 0:

            return None


        return {

            "alert": "MISSING_MILK_ENTRIES",

            "missing_animals": missing,

            "severity": "HIGH",

        }



    def production_alert(
        self,
        actual,
        expected
    ):


        if expected <= 0:

            return None


        deviation = (
            expected - actual
        ) / expected * 100



        if deviation < 20:

            return None



        return {

            "alert": "LOW_MILK_PRODUCTION",

            "deviation_percentage": round(
                deviation,
                2
            ),

            "severity": "MEDIUM",

        }
