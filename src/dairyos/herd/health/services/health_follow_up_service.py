class HealthFollowUpService:



    def __init__(self):

        self.followups = []



    def create(

        self,

        followup

    ):

        self.followups.append(

            followup

        )

        return followup



    def pending(

        self

    ):

        return [

            item

            for item in self.followups

            if item.completed is False

        ]



    def complete(

        self,

        followup

    ):

        followup.completed = True

        return followup
