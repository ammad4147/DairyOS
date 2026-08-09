from dataclasses import dataclass



@dataclass
class NavigationContext:

    level: str

    entity_type: str

    entity_id: str | None = None

    parent_id: str | None = None

