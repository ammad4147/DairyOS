from dairyos.intelligence.kernel.context.intelligence_context import (
    IntelligenceContext,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.kernel.interface.intelligence_gateway import (
    IntelligenceGateway,
)

from dairyos.intelligence.repository.intelligence_repository import (
    IntelligenceRepository,
)

from dairyos.intelligence.persistence.services.event_recorder import (
    EventRecorder,
)


class IntelligenceService:
    """
    Enterprise service boundary for DairyOS intelligence operations.

    Responsibilities:

    - accept intelligence signals
    - manage intelligence context
    - invoke intelligence gateway
    - persist intelligence records
    - record intelligence history
    - return structured intelligence results

    This layer separates enterprise services
    from the internal intelligence kernel.
    """


    def __init__(
        self,
        repository: IntelligenceRepository | None = None,
        event_repository=None,
    ):

        self.gateway = IntelligenceGateway()

        self.context = IntelligenceContext()

        self.repository = repository

        self.event_recorder = None


        if event_repository:

            self.event_recorder = EventRecorder(
                event_repository
            )


    def submit_signal(
        self,
        signal: IntelligenceSignal,
    ):

        self.context.add_signal(
            signal
        )


        if self.repository:

            self.repository.save_signal(
                signal
            )


        if self.event_recorder:

            self.event_recorder.record(
                event_type="signal_received",
                source=signal.source,
                payload={
                    "category": signal.category,
                    "message": signal.message,
                    "severity": signal.severity,
                },
            )


        return signal


    def process(
        self,
    ) -> dict:

        result = self.gateway.process(
            self.context
        )


        if self.repository:

            for decision in result.get(
                "decisions",
                [],
            ):

                self.repository.save_decision(
                    decision
                )


            for outcome in result.get(
                "outcomes",
                [],
            ):

                self.repository.save_outcome(
                    outcome
                )


        if self.event_recorder:

            self.event_recorder.record(
                event_type="intelligence_processed",
                source="intelligence_service",
                payload=result,
            )


        return result
