from dataclasses import dataclass



@dataclass
class SecurityContext:

    user_id: str

    role: str

    permissions: list[str]

