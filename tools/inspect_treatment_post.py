from pathlib import Path

p = Path("src/dairyos/api/farm_data_entry.py")
txt = p.read_text(encoding="utf-8")
lines = txt.splitlines()

print("=== INSPECTING POST /treatments HANDLER ===")
for i, line in enumerate(lines, start=1):
    if "@router.post(\"/treatments\")" in line or "@router.post('/treatments')" in line:
        start = max(0, i - 1)
        end = min(len(lines), i + 45)
        for j in range(start, end):
            print(f"{j+1:3d}: {lines[j]}")
        break