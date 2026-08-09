from enum import Enum



class FeedbackType(str, Enum):

    SUCCESS = "success"

    FAILURE = "failure"

    PARTIAL = "partial"

    UNKNOWN = "unknown"

