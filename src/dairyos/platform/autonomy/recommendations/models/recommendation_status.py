from enum import Enum



class RecommendationStatus(str, Enum):

    NEW = "new"

    REVIEWED = "reviewed"

    APPROVED = "approved"

    EXECUTED = "executed"

    REJECTED = "rejected"

