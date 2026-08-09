from ..models.medicine_inventory import MedicineInventory



class MedicineInventoryService:



    def evaluate(

        self,

        medicine_name,

        available_units,

        monthly_consumption

    ):


        if monthly_consumption > 0:

            coverage_months = (

                available_units /

                monthly_consumption

            )

        else:

            coverage_months = 0



        if coverage_months >= 3:

            status = "SECURE"

            action = "Continue normal procurement"


        elif coverage_months >= 1:

            status = "MONITOR"

            action = "Review upcoming purchase"


        else:

            status = "CRITICAL"

            action = "Immediate medicine procurement required"



        return MedicineInventory(

            medicine_name,

            available_units,

            monthly_consumption,

            coverage_months,

            status,

            action

        )
