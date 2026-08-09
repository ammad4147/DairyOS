from dataclasses import dataclass, field

from dairyos.farm.command_center.models.farm_status_snapshot import (
    FarmStatusSnapshot,
)


@dataclass
class OperationalCommandCenter:
    """
    Unified operational snapshot returned by the
    Operational Command Center.

    This is a composition model only.
    It owns no business logic.
    """

    farm_status: FarmStatusSnapshot = field(
        default_factory=FarmStatusSnapshot
    )

    health: dict = field(default_factory=dict)

    dashboard: dict = field(default_factory=dict)

    notifications: list = field(default_factory=list)

    decisions: dict = field(default_factory=dict)

    execution: dict = field(default_factory=dict)

    intelligence: dict = field(default_factory=dict)
