from ..models.feed_inventory import FeedInventory



class FeedInventoryService:



    def evaluate(

        self,

        feed_item,

        available_quantity,

        daily_consumption

    ):


        if daily_consumption > 0:

            coverage_days = (

                available_quantity /

                daily_consumption

            )

        else:

            coverage_days = 0



        if coverage_days >= 30:

            status = "SECURE"

            action = "Continue normal procurement"


        elif coverage_days >= 7:

            status = "MONITOR"

            action = "Review upcoming purchase"


        else:

            status = "CRITICAL"

            action = "Immediate feed procurement required"



        return FeedInventory(

            feed_item,

            available_quantity,

            daily_consumption,

            coverage_days,

            status,

            action

        )
