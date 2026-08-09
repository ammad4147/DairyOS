from ..models.decision_memory import DecisionMemory



class DecisionMemoryService:



    def __init__(self):

        self.memory = []



    def record(

        self,

        decision_id,

        category,

        decision,

        reason,

        priority,

        owner,

        status="PENDING",

        outcome=""

    ):


        item = DecisionMemory(

            decision_id,

            category,

            decision,

            reason,

            priority,

            owner,

            status,

            outcome

        )


        self.memory.append(item)


        return item



    def get_all(self):

        return self.memory



    def find_by_category(

        self,

        category

    ):


        return [

            item

            for item in self.memory

            if item.category == category

        ]



    def completed_decisions(self):

        return [

            item

            for item in self.memory

            if item.status == "COMPLETED"

        ]
