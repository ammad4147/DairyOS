from dataclasses import dataclass

from dairyos.platform.digital_twin.models.herd_state import (
    HerdState,
)

from dairyos.platform.digital_twin.models.operational_state import (
    OperationalState,
)



@dataclass
class FarmState:

    farm_id: str

    herd: HerdState

    operations: OperationalState

    milk_production_daily: float

    revenue_daily: float

    expense_daily: float

    risk_level: str

