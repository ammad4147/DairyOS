from dataclasses import dataclass

from .entity_reference import EntityReference


@dataclass
class EntityContext:
    entity: EntityReference
    department: str
    status: str
    metadata: dict
