class AnimalDeviationService:



    def percentage_change(

        self,

        baseline,

        current

    ):

        if baseline == 0:

            return 0


        return (

            (baseline - current)

            /

            baseline

        ) * 100



    def evaluate_milk(

        self,

        baseline,

        current

    ):

        change = self.percentage_change(

            baseline,

            current

        )


        if change >= 20:

            return "HIGH"


        if change >= 10:

            return "MEDIUM"


        return "NORMAL"



    def evaluate_feed(

        self,

        baseline,

        current

    ):

        change = self.percentage_change(

            baseline,

            current

        )


        if change >= 20:

            return "HIGH"


        if change >= 10:

            return "MEDIUM"


        return "NORMAL"
