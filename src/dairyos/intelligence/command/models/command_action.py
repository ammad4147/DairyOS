from dataclasses import dataclass


@dataclass
class CommandAction:
    """
    Represents an autonomous command action.
    """


    action_id: str

    recommendation_id: str

    action_type: str

    status: str
