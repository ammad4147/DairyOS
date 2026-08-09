from dataclasses import dataclass



@dataclass
class EventSubscription:
    """
    Defines a subscriber interested in
    operational events.
    """

    event_type: str

    handler: object
