from dataclasses import dataclass


@dataclass
class AuthorizationRequest:
    """
    Incoming authorization evaluation request.
    """

    user_id: str
    tenant_id: str
    resource: str
    action: str
    role: str
