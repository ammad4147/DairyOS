from dataclasses import dataclass


@dataclass
class ActionAssignment:
    """
    Represents assignment ownership
    for an operational action.

    Future extensions:

    - workload balancing
    - staff availability
    - role permissions
    """


    action_type: str

    assigned_to: str

    assigned_role: str

    status: str
