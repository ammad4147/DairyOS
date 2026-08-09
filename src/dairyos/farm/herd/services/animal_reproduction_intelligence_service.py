from dairyos.farm.herd.models.animal_operational_state import (
    AnimalOperationalState,
)


class AnimalReproductionIntelligenceService:
    """
    Operational intelligence for animal reproduction.

    Converts reproduction state into actionable
    farm attention items.

    This is rule-based operational intelligence.

    No breeding business rules belong here.
    Events remain the source of truth.
    """

    def evaluate(
        self,
        state: AnimalOperationalState,
    ) -> AnimalOperationalState:
        """
        Evaluate reproductive condition.
        """

        self._check_heat(
            state
        )

        self._check_pregnancy_confirmation(
            state
        )

        self._check_failed_attempts(
            state
        )

        return state



    def _check_heat(
        self,
        state,
    ):
        """
        Detect heat requiring action.
        """

        if (
            state.reproduction_status
            ==
            "HEAT_DETECTED"
        ):

            state.add_attention(
                "Heat detected - breeding action required"
            )



    def _check_pregnancy_confirmation(
        self,
        state,
    ):
        """
        Detect pending pregnancy checks.
        """

        if (
            state.pregnancy_status
            ==
            "PENDING_CONFIRMATION"
        ):

            state.add_attention(
                "Pregnancy confirmation required"
            )



    def _check_failed_attempts(
        self,
        state,
    ):
        """
        Detect repeated breeding attempts.
        """

        if (
            state.breeding_attempts >= 3
        ):

            state.add_attention(
                "Multiple breeding attempts - fertility review required"
            )
