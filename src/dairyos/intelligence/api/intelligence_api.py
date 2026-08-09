from dairyos.intelligence.services.intelligence_service import (
    IntelligenceService,
)


class IntelligenceAPI:
    """
    Enterprise application boundary for
    DairyOS intelligence operations.

    Responsibilities:

    - receive intelligence requests
    - submit signals
    - trigger intelligence processing
    - expose autonomous intelligence execution

    This layer does not contain intelligence logic.
    """


    def __init__(
        self,
        service: IntelligenceService | None = None,
        autonomous_service=None,
    ):

        self.service = (
            service
            if service
            else IntelligenceService()
        )


        if autonomous_service is None:

            from dairyos.intelligence.application.autonomous_intelligence_service import (
                AutonomousIntelligenceService,
            )

            autonomous_service = AutonomousIntelligenceService()


        self.autonomous_service = (
            autonomous_service
        )



    def submit_signal(
        self,
        signal,
    ):

        return self.service.submit_signal(
            signal
        )



    def process(
        self,
    ) -> dict:

        return self.service.process()



    def execute_autonomous_cycle(
        self,
        context=None,
    ):

        return self.autonomous_service.execute_cycle(
            context
        )



    def get_autonomous_history(
        self,
    ):

        return self.autonomous_service.get_cycle_history()



    def get_autonomous_cycle(
        self,
        cycle_id: str,
    ):

        return self.autonomous_service.get_cycle(
            cycle_id
        )



    def get_autonomous_status(
        self,
    ):

        return self.autonomous_service.get_runtime_status()
