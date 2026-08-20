from pathlib import Path

p = Path("src/dairyos/api/reproduction_management.py")
lines = p.read_text(encoding="utf-8").splitlines()

print(f"=== {p} (Lines 30-95) ===")
for i, line in enumerate(lines[29:95], start=30):
    print(f"{i:3d}: {line}")