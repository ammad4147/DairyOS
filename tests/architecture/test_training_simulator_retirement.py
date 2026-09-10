from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "src" / "DairyOS.Web" / "src"


def test_training_simulator_is_removed_from_the_operator_surface():
    settings = (WEB / "components" / "SettingsTab.tsx").read_text(
        encoding="utf-8-sig"
    )
    assistant = (WEB / "components" / "DairyOSAssistant.tsx").read_text(
        encoding="utf-8-sig"
    )

    assert not (WEB / "components" / "TrainingSimulator.tsx").exists()
    assert "TrainingSimulator" not in settings
    assert "TRAINING" not in settings
    assert "Training Simulator" not in settings
    assert "Training Simulator" not in assistant
