class ProductionService:



    def __init__(self):

        self.records = []

        self.groups = []



    def record_milk(

        self,

        record

    ):

        self.records.append(record)

        return record



    def add_group(

        self,

        group

    ):

        self.groups.append(group)

        return group



    def milk_record_count(self):

        return len(self.records)



    def group_count(self):

        return len(self.groups)
