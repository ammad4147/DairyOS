from dataclasses import dataclass
from datetime import datetime, timezone

from dairyos.platform.tenant_admin.models.tenant_status import (
    TenantStatus,
)



@dataclass
class Tenant:

    tenant_id: str

    name: str

    status: TenantStatus = TenantStatus.PROVISIONING

    created_at: datetime = datetime.now(timezone.utc)
