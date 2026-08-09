from dataclasses import dataclass, field


@dataclass
class FarmStatusSnapshot:
    """
    High-level operational snapshot.

    This is the primary object displayed
    on the Farm Command Center.
    """

    milk: dict = field(default_factory=dict)

    feeding: dict = field(default_factory=dict)

    breeding: dict = field(default_factory=dict)

    health: dict = field(default_factory=dict)

    inventory: dict = field(default_factory=dict)

    equipment: dict = field(default_factory=dict)

    workforce: dict = field(default_factory=dict)

    finance: dict = field(default_factory=dict)

    attention_queue: list = field(default_factory=list)
