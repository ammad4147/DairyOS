from dataclasses import dataclass, field
from datetime import datetime, timezone



@dataclass
class WorkforceCommandSnapshot:
    """
    Unified workforce intelligence command snapshot.

    Consolidates workforce execution,
    performance,
    reliability,
    accountability,
    and ownership intelligence
    for command center consumption.
    """


    execution_health: str = "GREEN"


    performance_status: str = "GREEN"


    reliability_status: str = "HIGH"


    accountability_status: str = "HIGH"


    ownership_status: str = "HIGH"


    execution_score: float = 100.0


    performance_score: float = 100.0


    reliability_score: float = 100.0


    accountability_score: float = 100.0


    ownership_score: float = 100.0


    management_attention_required: bool = False


    priority_level: str = "NORMAL"


    recommended_action: str = (
        "Maintain workforce operational performance"
    )


    generated_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )
