from ..models.tenant import Tenant
from ..models.tenant_membership import TenantMembership


class TenantService:
    """
    Enterprise tenant lifecycle manager.
    """

    def __init__(self):
        self._tenants: dict[str, Tenant] = {}
        self._memberships: list[TenantMembership] = []

    def create(
        self,
        tenant: Tenant
    ) -> Tenant:

        self._tenants[
            tenant.tenant_id
        ] = tenant

        return tenant

    def get(
        self,
        tenant_id: str
    ) -> Tenant | None:

        return self._tenants.get(
            tenant_id
        )

    def add_member(
        self,
        membership: TenantMembership
    ) -> None:

        self._memberships.append(
            membership
        )

    def members(
        self,
        tenant_id: str
    ) -> list[TenantMembership]:

        return [
            membership
            for membership in self._memberships
            if membership.tenant_id == tenant_id
        ]
