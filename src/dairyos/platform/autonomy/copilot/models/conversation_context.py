from dataclasses import dataclass



@dataclass
class ConversationContext:

    user_id: str

    role: str

    farm_id: str

    session_id: str

