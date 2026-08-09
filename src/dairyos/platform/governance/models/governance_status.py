from enum import Enum


class GovernanceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVIEW = "review"
