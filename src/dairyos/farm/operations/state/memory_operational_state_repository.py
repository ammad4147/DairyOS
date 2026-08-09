from dairyos.farm.operations.state.operational_state_repository import (
    OperationalStateRepository,
)

from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class MemoryOperationalStateRepository(
    OperationalStateRepository
):
    """
    In-memory persistence adapter
    for current operational state.
    """


    def __init__(
        self,
    ):

        self.states = {}



    def load(
        self,
        farm_id: str,
    ) -> FarmOperationalState | None:

        return self.states.get(
            farm_id
        )



    def get_current(
        self,
        farm_id: str,
    ) -> FarmOperationalState | None:

        return self.states.get(
            farm_id
        )



    def save(
        self,
        state: FarmOperationalState,
    ) -> FarmOperationalState:

        self.states[
            state.farm_id
        ] = state


        return state
