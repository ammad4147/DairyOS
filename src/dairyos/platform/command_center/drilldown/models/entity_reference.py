from dataclasses import dataclass



@dataclass
class EntityReference:

    entity_type: str

    entity_id: str

    display_name: str

