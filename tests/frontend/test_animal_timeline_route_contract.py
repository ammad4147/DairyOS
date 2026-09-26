from pathlib import Path


def test_animal_context_uses_mounted_passport_timeline_route():
    repository_root = Path(__file__).resolve().parents[2]
    context = (
        repository_root
        / "src"
        / "DairyOS.Web"
        / "src"
        / "context"
        / "AnimalContext.tsx"
    ).read_text(encoding="utf-8")

    assert "/farm/animals/${encodeURIComponent(selectedAnimalId)}/timeline" in context
    assert "/api/v2/animals/${encodeURIComponent(selectedAnimalId)}/timeline" not in context
