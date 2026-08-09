from dataclasses import dataclass
from enum import Enum


class AccessDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class AuthorizationResult:

    decision: AccessDecision

    reason: str

    subject: str

    resource: str
