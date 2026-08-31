from pathlib import Path


def test_digital_twin_structure():
    root = Path("src/dairyos/platform/digital_twin")

    assert root.exists()

    required = [
        "models",
        "forecasting",
        "decision",
        "presentation",
        "persistence",
        "services",
        "synchronization",
        "integration",
    ]

    for folder in required:
        assert (root / folder).is_dir()
