from dataclasses import dataclass



@dataclass
class FarmEvent:


    event_id: str

    event_type: str

    source_module: str

    entity_id: str

    value: float

    status: str
