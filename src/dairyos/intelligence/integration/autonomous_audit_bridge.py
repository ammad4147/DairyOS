"""
DairyOS Autonomous Audit Bridge

Connects autonomous intelligence runtime
with enterprise event infrastructure.

Responsibilities:

- receive completed autonomous cycles
- create standardized enterprise events
- adapt events for persistence
- preserve legacy audit contracts

Runtime orchestration remains independent.
"""


from dairyos.intelligence.events.services.autonomous_event_service import (
    AutonomousEventService,
)

from dairyos.intelligence.events.adapters.event_adapter import (
    EventAdapter,
)



class AutonomousAuditBridge:
    """
    Records autonomous intelligence cycles
    through enterprise event architecture.
    """


    def __init__(
        self,
        event_service=None,
        event_adapter=None,
        memory_gateway=None,
    ):

        if event_service is None:

            event_service = AutonomousEventService()


        if event_adapter is None:

            event_adapter = EventAdapter()


        if memory_gateway is None:

            from dairyos.intelligence.persistence.gateway.intelligence_memory_gateway import (
                IntelligenceMemoryGateway,
            )

            from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
                MemoryEventRepository,
            )


            memory_gateway = IntelligenceMemoryGateway(
                MemoryEventRepository()
            )


        self.event_service = event_service

        self.event_adapter = event_adapter

        self.memory_gateway = memory_gateway



    def record_cycle(
        self,
        result: dict,
    ):

        runtime = result.get(
            "runtime",
            {},
        )


        validation = result.get(
            "runtime_validation"
        )


        enterprise_event = (
            self.event_service.cycle_completed(
                runtime,
                validation,
            )
        )


        adapted_event = (
            self.event_adapter.adapt(
                enterprise_event
            )
        )


        payload = {
            **adapted_event["payload"],

            #
            # Legacy autonomous audit compatibility
            #
            "cycle_id": adapted_event["entity_id"],

            "event_id": adapted_event["event_id"],

            "correlation_id": adapted_event["correlation_id"],

            "entity_type": adapted_event["entity_type"],

            "entity_id": adapted_event["entity_id"],

            "actor": adapted_event["actor"],

            "severity": adapted_event["severity"],
        }


        return self.memory_gateway.record(
            event_type=adapted_event["event_type"],

            source=adapted_event["source"],

            payload=payload,
        )
