from dataclasses import dataclass



@dataclass
class EntityContext:

    entity: EntityReference

    department: str

    status: str

    metadata: dict

