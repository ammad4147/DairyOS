from dataclasses import dataclass


@dataclass
class ExecutionRecord:
    """
    Represents operational execution tracking.

    Future extensions:

    - execution timestamps
    - evidence capture
    - completion verification
    """


    action_type: str

    performed_by: str

    execution_status: str

    notes: str
