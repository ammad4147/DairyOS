from dataclasses import dataclass
from datetime import datetime, timezone

from dairyos.platform.governance.models.governance_status import GovernanceStatus


@dataclass
class GovernancePolicy:
    policy_id: str
    name: str
    description: str
    status: GovernanceStatus = GovernanceStatus.ACTIVE
    created_at: datetime = datetime.now(timezone.utc)
