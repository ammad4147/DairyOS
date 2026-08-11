from dairyos.farm.operations.events.farm_operation_event_bridge import (
    FarmOperationEventBridge,
)


class OperationalEventAdapter(FarmOperationEventBridge):
    """
    Backwards-compatible name for the canonical
    FarmOperationEventBridge.

    The adapter intentionally contains no separate translation logic.

    Canonical implementation:

        FarmOperationEventBridge

    This compatibility class exists so older construction and import
    paths continue to function without creating a second adapter
    implementation.
    """

    pass
