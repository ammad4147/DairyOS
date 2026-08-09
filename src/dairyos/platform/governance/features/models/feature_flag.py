from dataclasses import dataclass



@dataclass
class FeatureFlag:

    """
    Enterprise feature activation control.
    """

    key: str

    enabled: bool = False

    description: str = ""
