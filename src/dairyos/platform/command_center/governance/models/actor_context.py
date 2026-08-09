from dataclasses import dataclass



@dataclass
class ActorContext:

    user_id: str

    role: str

    tenant_id: str

