from pathlib import Path

p = Path("src/dairyos/herd/reproduction/services/reproductive_event_classifier.py")
lines = p.read_text(encoding="utf-8").splitlines()

print(f"=== {p} ===")
for i, line in enumerate(lines, start=1):
    print(f"{i:3d}: {line}")