from dataclasses import dataclass


@dataclass
class TenantMembership:
    """
    Connects users to enterprise tenants.
    """

    tenant_id: str

    user_id: str

    role: str
