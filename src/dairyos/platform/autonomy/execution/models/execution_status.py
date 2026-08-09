from enum import Enum



class ExecutionStatus(str, Enum):

    DRAFT = "draft"

    PENDING_APPROVAL = "pending_approval"

    APPROVED = "approved"

    EXECUTING = "executing"

    COMPLETED = "completed"

    REJECTED = "rejected"

