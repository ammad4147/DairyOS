from pathlib import Path


def test_digital_twin_structure():

    root = Path(
        "src/dairyos/platform/digital_twin"
    )

    assert root.exists()

    required = [

        "models",
        "simulation",
        "forecasting",
        "decision",
        "presentation",
        "persistence",
        "services",

    ]

    for folder in required:

        assert (
            root / folder
        ).exists()
