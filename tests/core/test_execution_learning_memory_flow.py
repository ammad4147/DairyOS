"""
DairyOS Sprint 025

Execution ? Learning ? Memory
Integration Validation
"""


def test_execution_learning_memory_chain():

    from dairyos.intelligence.execution.gateway.execution_gateway import (
        ExecutionGateway,
    )

    from dairyos.intelligence.learning.gateway.learning_gateway import (
        LearningGateway,
    )

    from dairyos.intelligence.memory.gateway.memory_gateway import (
        MemoryGateway,
    )


    execution = ExecutionGateway()

    learning = LearningGateway()

    memory = MemoryGateway()


    assert execution is not None
    assert learning is not None
    assert memory is not None
