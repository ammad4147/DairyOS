from pathlib import Path

p = Path("src/dairyos/api/animal_registration.py")
lines = p.read_text(encoding="utf-8").splitlines()

print("=== ALLOWED REGISTRATION FIELDS & LIFECYCLE ENUMS ===")
for i, line in enumerate(lines[95:155], start=96):
    print(f"{i:3d}: {line}")