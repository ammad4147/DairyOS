from dataclasses import dataclass



@dataclass
class ResourceLimit:

    tenant_id: str

    resource_type: str

    maximum: int
