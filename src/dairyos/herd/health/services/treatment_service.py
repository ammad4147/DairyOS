class TreatmentService:



    def __init__(self):

        self.treatments = []



    def create(

        self,

        treatment

    ):

        self.treatments.append(

            treatment

        )

        return treatment



    def get_animal_treatments(

        self,

        animal_id

    ):

        return [

            item

            for item in self.treatments

            if item.animal_id == animal_id

        ]



    def complete(

        self,

        treatment

    ):

        treatment.status = "COMPLETED"

        return treatment
