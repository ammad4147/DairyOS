from dataclasses import dataclass


@dataclass
class MemoryContext:
    """
    Represents contextual information associated
    with intelligence memory.

    Future extensions:

    - context hierarchy
    - session correlation
    - operational scope
    """


    context_id: str

    context_type: str

    description: str

    owner: str
