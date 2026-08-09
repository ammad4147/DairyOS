from ..models.dashboard import HerdDashboard



class HerdDashboardService:



    def generate(

        self,

        farm_name,

        snapshot,

        capacity

    ):


        return HerdDashboard(

            farm_name=farm_name,

            total_animals=snapshot.total_animals,

            milking_cows=snapshot.milking_cows,

            dry_cows=snapshot.dry_cows,

            heifers=snapshot.heifers,

            calves=snapshot.calves,

            capacity=capacity

        )
