from dairyos.platform.domain_health.models.domain_health_status import (
    DomainHealthStatus,
)



class DomainHealthService:
    """
    Enterprise operational domain health federation.
    """



    def __init__(
        self,
        registry,
    ):

        self.registry = registry



    def evaluate(self):

        domains = self.registry.list_domains()


        return [

            DomainHealthStatus(

                domain=domain.name,

                status="healthy",

                message="Domain operational",

            )

            for domain in domains

        ]



    def summary(self):

        health = self.evaluate()


        return {

            "status": "healthy",

            "domains": [

                {

                    "domain": item.domain,

                    "status": item.status,

                }

                for item in health

            ]

        }
