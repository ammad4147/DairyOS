from dataclasses import dataclass


@dataclass
class MemoryEvent:
    """
    Represents a memory-producing event.

    Future extensions:

    - event timestamps
    - event correlation
    - event replay
    """


    event_id: str

    event_type: str

    description: str

    source: str
