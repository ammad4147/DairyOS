from enum import Enum



class RelationshipType(Enum):

    OWNS = "owns"

    BELONGS_TO = "belongs_to"

    HAS_HEALTH_EVENT = "has_health_event"

    PRODUCES = "produces"

    AFFECTS = "affects"

    CAUSES = "causes"

    IMPACTS = "impacts"

    CORRELATED_WITH = "correlated_with"

