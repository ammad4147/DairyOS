from ..models.herd_context import HerdContext



class HerdAggregator:



    def build(

        self,

        farm_name,

        total_animals,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False,

        production_status="STABLE",

        financial_status="POSITIVE",

        feed_status="NORMAL"

    ):


        return HerdContext(

            farm_name=farm_name,

            total_animals=total_animals,

            health_alerts=health_alerts,

            open_cows=open_cows,

            replacement_shortage=replacement_shortage,

            production_status=production_status,

            financial_status=financial_status,

            feed_status=feed_status

        )



    def from_snapshot(

        self,

        snapshot,

        farm_name,

        total_animals

    ):


        financial_status = "POSITIVE"


        if snapshot.costs > 0 and snapshot.revenues == 0:

            financial_status = "WARNING"



        feed_status = "NORMAL"


        if snapshot.feed_plans == 0:

            feed_status = "UNKNOWN"



        return HerdContext(

            farm_name=farm_name,

            total_animals=total_animals,

            health_alerts=snapshot.health_events,

            production_status=(

                "ACTIVE"

                if snapshot.milk_records > 0

                else "INACTIVE"

            ),

            financial_status=financial_status,

            feed_status=feed_status

        )
