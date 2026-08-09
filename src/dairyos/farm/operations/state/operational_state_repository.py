from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class OperationalStateRepository:
    """
    Persistence boundary for current farm operational state.

    Stores current operational truth.

    Historical events remain separate.
    """


    def __init__(
        self,
    ):

        self._state = None



    def get_current(
        self,
        farm_id: str,
    ) -> FarmOperationalState | None:

        if self._state is None:

            return None


        if self._state.farm_id != farm_id:

            return None


        return self._state



    def load(
        self,
        farm_id: str = "DEFAULT",
    ) -> FarmOperationalState | None:
        """
        Repository read contract.

        Compatibility layer for dashboard,
        bootstrap and persistence services.
        """

        return self.get_current(
            farm_id
        )



    def save(
        self,
        state: FarmOperationalState,
    ):

        self._state = state

        return state



    def save_state(
        self,
        state: FarmOperationalState,
    ):

        return self.save(
            state
        )



    def get_state(
        self,
    ):

        return self._state
