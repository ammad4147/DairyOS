from dairyos.intelligence.integration.connectors.learning_memory_connector import (
    LearningMemoryConnector,
)


def test_learning_memory_connector():

    connector = LearningMemoryConnector()

    result = connector.store(
        "learning-001"
    )

    assert result["learning"] == "learning-001"
    assert result["status"] == "stored"
