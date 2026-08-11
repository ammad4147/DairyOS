from dataclasses import dataclass


@dataclass
class ExecutionPlan:
    """
    Intelligence planning artifact.

    ExecutionPlan answers how proposed work should be prepared and
    coordinated. It is not the record of work actually performed.

    The architectural hand-off is:

        Recommendation / decision
                |
                v
          ExecutionPlan
                |
          approved / accepted
                v
        OperationalAction
                |
                v
          Assignment
                |
                v
      OperationalExecution

    Only OperationalExecution owns the operational execution lifecycle.
    """

    workflow_type: str
    objective: str
    priority: str
    status: str
