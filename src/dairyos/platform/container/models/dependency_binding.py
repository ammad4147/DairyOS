from dataclasses import dataclass


@dataclass
class DependencyBinding:
    """
    Maps a dependency name to an implementation.
    """

    interface: str

    implementation: object
