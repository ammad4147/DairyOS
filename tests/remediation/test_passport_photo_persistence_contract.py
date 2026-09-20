from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PASSPORT = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "AnimalPassportModal.tsx"


def test_passport_restores_saved_photo_when_reopened():
    source = PASSPORT.read_text(encoding="utf-8")
    assert "setPhotoData(animalData.photo_data||null)" in source
    assert "accept=\"image/jpeg,image/png,image/webp\"" in source

