from ..models.animal_inventory import AnimalInventory



class AnimalInventoryService:



    def evaluate(

        self,

        animal_id,

        breed,

        age_months,

        category

    ):


        if age_months < 12:

            lifecycle_status = "CALF"


        elif age_months < 24:

            lifecycle_status = "HEIFER"


        elif category.lower() == "pregnant heifer":

            lifecycle_status = "PRE-CALVING"


        elif category.lower() == "lactating cow":

            lifecycle_status = "LACTATING"


        else:

            lifecycle_status = "ACTIVE"



        return AnimalInventory(

            animal_id,

            breed,

            age_months,

            category,

            lifecycle_status,

            "ACTIVE"

        )
