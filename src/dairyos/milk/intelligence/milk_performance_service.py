from collections import defaultdict


class MilkPerformanceService:


    def summarize(
        self,
        entries
    ):

        total_litres = sum(
            entry.litres
            for entry in entries
        )


        animals = len(
            set(
                entry.animal_id
                for entry in entries
            )
        )


        sessions = defaultdict(float)


        for entry in entries:

            sessions[
                entry.session.value
            ] += entry.litres



        average_yield = 0


        if animals:

            average_yield = round(
                total_litres / animals,
                2
            )


        return {

            "total_litres": total_litres,

            "animals_milked": animals,

            "average_yield": average_yield,

            "session_breakdown": dict(
                sessions
            ),

        }


    def animal_yield_ranking(
        self,
        entries
    ):

        animals = defaultdict(float)


        for entry in entries:

            animals[
                entry.animal_id
            ] += entry.litres


        return sorted(

            animals.items(),

            key=lambda item: item[1],

            reverse=True

        )
