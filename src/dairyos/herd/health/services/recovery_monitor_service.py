class RecoveryMonitorService:



    def __init__(self):

        self.responses = []

        self.outcomes = []



    def record_response(

        self,

        response

    ):

        self.responses.append(

            response

        )

        return response



    def record_outcome(

        self,

        outcome

    ):

        self.outcomes.append(

            outcome

        )

        return outcome



    def get_responses(

        self,

        animal_id

    ):

        return [

            item

            for item in self.responses

            if item.animal_id == animal_id

        ]
