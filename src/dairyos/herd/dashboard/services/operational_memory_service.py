from ..models.operational_memory import OperationalMemory



class OperationalMemoryService:



    def __init__(self):

        self.records = []



    def record_intervention(

        self,

        category,

        issue,

        action,

        status="COMPLETED",

        outcome=""

        ,

        priority="MEDIUM"

    ):


        record = OperationalMemory(

            category,

            issue,

            action,

            status,

            outcome,

            priority

        )


        self.records.append(record)


        return record



    def history_count(self):

        return len(self.records)



    def get_history(self):

        return self.records



    def completed_actions(self):

        return [

            item

            for item in self.records

            if item.status == "COMPLETED"

        ]
