from ..models.performance_metric import PerformanceMetric



class PerformanceAnalyticsService:



    def calculate(

        self,

        total_actions,

        completed_actions

    ):


        open_actions = total_actions - completed_actions


        if total_actions == 0:

            completion_rate = 0

        else:

            completion_rate = round(

                (completed_actions / total_actions) * 100,

                2

            )


        effectiveness = round(

            completion_rate

        )


        return PerformanceMetric(

            total_actions,

            completed_actions,

            open_actions,

            completion_rate,

            effectiveness

        )



    def category_count(

        self,

        records

    ):


        result = {}


        for item in records:

            if item.category not in result:

                result[item.category] = 0


            result[item.category] += 1


        return result



    def most_frequent_category(

        self,

        records

    ):


        counts = self.category_count(records)


        if not counts:

            return None


        return max(

            counts,

            key=counts.get

        )
