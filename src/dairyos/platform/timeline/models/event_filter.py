from dataclasses import dataclass



@dataclass
class EventFilter:

    entity_type: str

    entity_id: str | None = None

    event_type: str | None = None

