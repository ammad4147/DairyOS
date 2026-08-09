class MilkValidationService:


    def validate_register(
        self,
        register,
        expected_animals: int
    ):


        problems = []


        if register.animals_recorded() < expected_animals:

            problems.append(
                "Missing animal milk entries"
            )


        if register.total_litres() <= 0:

            problems.append(
                "No milk production recorded"
            )


        if not register.verified:

            problems.append(
                "Register not verified"
            )


        return problems



    def is_ready(
        self,
        register,
        expected_animals
    ):

        return len(
            self.validate_register(
                register,
                expected_animals
            )
        ) == 0
