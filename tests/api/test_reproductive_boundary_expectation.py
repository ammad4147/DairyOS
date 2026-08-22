from datetime import date

from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


def expected_reproductive_state_for_today(last_calving_value):
    """Return the contract state without depending on runner wall-clock assumptions."""
    if not last_calving_value:
        return "UNKNOWN"
    calving_date = date.fromisoformat(str(last_calving_value)[:10])
    operational_date = OperationalDateAuthority().current_date()
    return "CALVED" if calving_date == operational_date else "LACTATING"
