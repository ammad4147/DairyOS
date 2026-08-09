from dairyos.farm.herd.models.animal_operational_state import (
    AnimalOperationalState,
)

from dairyos.farm.herd.services.animal_reproduction_intelligence_service import (
    AnimalReproductionIntelligenceService,
)


class AnimalIntelligenceService:
    """
    Operational decision engine for individual animals.

    Converts animal operational state into
    actionable farm attention items.

    This is rule-based intelligence.

    Future AI models may enhance recommendations,
    but operational truth comes from recorded data.
    """



    def __init__(
        self,
        reproduction_intelligence_service=None,
    ):

        self.reproduction_intelligence_service = (

            reproduction_intelligence_service

            if reproduction_intelligence_service

            else AnimalReproductionIntelligenceService()

        )



    def evaluate(
        self,
        state: AnimalOperationalState,
    ) -> AnimalOperationalState:
        """
        Evaluates current animal condition.
        """

        state.clear_attention()



        self._check_milk_performance(
            state
        )


        self._check_health(
            state
        )


        self._check_reproduction(
            state
        )


        return state



    def _check_milk_performance(
        self,
        state,
    ):
        """
        Detect production decline.
        """

        deviation = (
            state.calculate_milk_deviation()
        )


        if deviation <= -15:

            state.add_attention(
                "Milk production below expected level"
            )



    def _check_health(
        self,
        state,
    ):
        """
        Detect health concerns.
        """

        if (
            state.health_status
            ==
            "ATTENTION_REQUIRED"
        ):

            state.add_attention(
                "Health review required"
            )



    def _check_reproduction(
        self,
        state,
    ):
        """
        Evaluate reproduction condition.
        """

        self.reproduction_intelligence_service.evaluate(
            state
        )



    def evaluate_all(
        self,
        states: list[AnimalOperationalState],
    ) -> list[AnimalOperationalState]:
        """
        Evaluates herd states.
        """

        return [
            self.evaluate(state)
            for state in states
        ]
