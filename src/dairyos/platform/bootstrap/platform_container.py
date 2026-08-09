from dairyos.platform.configuration.services.configuration_manager import (
    ConfigurationManager,
)

from dairyos.platform.authorization.services.authorization_service import (
    AuthorizationService,
)

from dairyos.platform.resources.services.resource_service import (
    ResourceService,
)

from dairyos.platform.tenant_admin.services.tenant_service import (
    TenantService,
)

from dairyos.platform.governance.services.governance_service import (
    GovernanceService,
)



class PlatformContainer:
    """
    Enterprise dependency composition container.
    """



    def __init__(self):

        self.configuration = ConfigurationManager()

        self.authorization = AuthorizationService()

        self.resources = ResourceService()

        self.tenants = TenantService()

        self.governance = GovernanceService()



    def health(self):

        return {

            "platform": "DairyOS",

            "components": {

                "configuration": "ready",

                "authorization": "ready",

                "resources": "ready",

                "tenants": "ready",

                "governance": "ready",

            }

        }
