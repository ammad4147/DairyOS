class NutritionService:



    def __init__(self):

        self.feed_plans = []

        self.consumptions = []



    def add_feed_plan(

        self,

        plan

    ):

        self.feed_plans.append(plan)

        return plan



    def record_consumption(

        self,

        consumption

    ):

        self.consumptions.append(consumption)

        return consumption



    def feed_plan_count(self):

        return len(self.feed_plans)



    def consumption_count(self):

        return len(self.consumptions)
