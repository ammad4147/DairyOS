from dairyos.platform.events_bridge.models.domain_event_mapping import (
    DomainEventMapping,
)



DEFAULT_EVENT_CATALOG = [

    DomainEventMapping(
        domain="herd",
        event_name="animal_registered",
        description="New animal entered herd",
    ),

    DomainEventMapping(
        domain="milk",
        event_name="milk_recorded",
        description="Milk production recorded",
    ),

    DomainEventMapping(
        domain="feed",
        event_name="feed_consumed",
        description="Feed consumption recorded",
    ),

    DomainEventMapping(
        domain="health",
        event_name="health_observation_created",
        description="Animal health event created",
    ),

    DomainEventMapping(
        domain="reproduction",
        event_name="breeding_event_created",
        description="Reproduction event created",
    ),

]
