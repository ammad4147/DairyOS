from dataclasses import dataclass



@dataclass
class ResourceUsage:

    tenant_id: str

    resource_type: str

    current: int = 0
