from pathlib import Path

# Let's inspect src/dairyos/api/farm_animals.py or wherever animal creation is handled
for p in Path("src/dairyos").rglob("*.py"):
    txt = p.read_text(encoding="utf-8")
    if "is system-generated and cannot be supplied" in txt:
        print(f"=== Found in {p} ===")
        lines = txt.splitlines()
        for i, line in enumerate(lines, start=1):
            if "system-generated" in line:
                start = max(1, i - 25)
                end = min(len(lines), i + 35)
                for j in range(start, end):
                    print(f"{j:3d}: {lines[j-1]}")