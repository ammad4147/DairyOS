class HerdSummaryService:


    def percentage(
        self,
        part,
        total
    ):

        if total == 0:

            return 0


        return round(

            (part / total) * 100,

            2

        )
