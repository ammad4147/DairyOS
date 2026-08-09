from dairyos.platform.tenant_admin.models.tenant import Tenant



class TenantService:
    """
    Enterprise tenant lifecycle service.
    """



    def __init__(self):

        self.tenants = {}



    def create(
        self,
        tenant: Tenant,
    ):

        self.tenants[
            tenant.tenant_id
        ] = tenant


        return tenant



    def get(
        self,
        tenant_id: str,
    ):

        return self.tenants.get(
            tenant_id
        )



    def list_all(self):

        return list(
            self.tenants.values()
        )
