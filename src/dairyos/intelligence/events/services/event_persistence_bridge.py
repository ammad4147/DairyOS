"""
DairyOS Event Persistence Bridge

Enterprise boundary between:

EnterpriseEvent
        |
        v
Persistence Gateway

Responsibilities:

- convert enterprise events into persistence records
- keep event architecture independent
- avoid runtime coupling with repositories
"""


from dairyos.intelligence.persistence.gateway.intelligence_memory_gateway import (
    IntelligenceMemoryGateway,
)



class EventPersistenceBridge:
    """
    Persists enterprise events through
    the intelligence memory boundary.
    """


    def __init__(
        self,
        memory_gateway=None,
    ):

        if memory_gateway is None:

            from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
                MemoryEventRepository,
            )


            memory_gateway = IntelligenceMemoryGateway(
                MemoryEventRepository()
            )


        self.memory_gateway = memory_gateway



    def persist(
        self,
        event,
    ):

        return self.memory_gateway.record(
            event_type=event.event_type,

            source=event.source,

            payload={
                "event_id": event.event_id,

                "correlation_id": (
                    event.correlation_id
                ),

                "actor": event.actor,

                "entity_type": (
                    event.entity_type
                ),

                "entity_id": (
                    event.entity_id
                ),

                "severity": (
                    event.severity
                ),

                "timestamp": (
                    event.timestamp
                ),

                "payload": (
                    event.payload
                ),
            },
        )
