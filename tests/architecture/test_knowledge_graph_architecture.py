from pathlib import Path


def test_knowledge_graph_structure():

    root = Path(
        "src/dairyos/platform/knowledge_graph"
    )

    assert root.exists()

    required = [

        "entities",
        "relationships",
        "graph",
        "reasoning",
        "services",
        "integration",

    ]

    for folder in required:

        assert (
            root / folder
        ).exists()
