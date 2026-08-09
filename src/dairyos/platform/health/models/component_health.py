from dataclasses import dataclass



@dataclass
class ComponentHealth:

    component: str

    status: str

    message: str
