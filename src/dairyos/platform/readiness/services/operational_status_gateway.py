from dairyos.platform.readiness.models.operational_status import (
    OperationalStatus,
)


class OperationalStatusGateway:
    """
    Unified DairyOS operational state evaluator.
    """

    def __init__(
        self,
        runtime,
        health_service,
        readiness_service,
        domain_health_service,
        observability_service,
    ):

        self.runtime = runtime
        self.health_service = health_service
        self.readiness_service = readiness_service
        self.domain_health_service = domain_health_service
        self.observability_service = observability_service



    def evaluate(self):

        health = self.health_service.summary()

        readiness = (
            self.readiness_service.validate()
        )

        domains = (
            self.domain_health_service.summary()
        )

        observability = (
            self.observability_service.summary()
        )


        return OperationalStatus(

            platform="DairyOS",

            runtime=self.runtime.status(),

            healthy=(
                health["status"]
                == "healthy"
            ),

            ready=readiness.ready,

            domains=domains,

            observability=observability,

        )
