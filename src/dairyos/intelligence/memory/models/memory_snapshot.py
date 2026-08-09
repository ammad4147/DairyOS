from dataclasses import dataclass


@dataclass
class MemorySnapshot:
    """
    Represents a captured memory state.

    Future extensions:

    - versioning
    - historical replay
    - state comparison
    """


    snapshot_id: str

    memory_count: int

    description: str

    created_by: str
