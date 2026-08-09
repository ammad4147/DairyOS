from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DashboardContract:
    """
    Stable UI-facing dashboard contract.

    This is the presentation boundary between
    DairyOS operational runtime and external clients.

    It does not create operational truth.
    It only exposes existing projections.
    """


    system: str = "DairyOS"

    module: str = "Farm Command Center"

    health: str = "UNKNOWN"

    farm_status: str = "UNKNOWN"

    operational_state: Dict[str, Any] = field(
        default_factory=dict
    )

    dashboard: Dict[str, Any] = field(
        default_factory=dict
    )

    operational_decisions: List[Any] = field(
        default_factory=list
    )

    operational_decision_summary: Dict[str, Any] = field(
        default_factory=dict
    )

    exceptions: List[Any] = field(
        default_factory=list
    )

    event_count: int = 0


    def to_dict(self):
        return {

            "system":
                self.system,

            "module":
                self.module,

            "health":
                self.health,

            "farm_status":
                self.farm_status,

            "operational_state":
                self.operational_state,

            "dashboard":
                self.dashboard,

            "operational_decisions":
                self.operational_decisions,

            "operational_decision_summary":
                self.operational_decision_summary,

            "exceptions":
                self.exceptions,

            "event_count":
                self.event_count,

        }
