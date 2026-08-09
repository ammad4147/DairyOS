from dairyos.platform.readiness.models.capability_status import (
    CapabilityStatus,
)

from dairyos.platform.readiness.models.readiness_report import (
    ReadinessReport,
)



class ReadinessService:
    """
    Enterprise platform readiness validator.
    """



    def __init__(self):

        self.capabilities = []



    def register(
        self,
        name,
        status="ready",
        message="",
    ):


        self.capabilities.append(

            CapabilityStatus(

                name=name,

                status=status,

                message=message,

            )

        )



    def validate(self):

        ready = all(

            item.status == "ready"

            for item in self.capabilities

        )


        return ReadinessReport(

            ready=ready,

            capabilities=self.capabilities,

        )

