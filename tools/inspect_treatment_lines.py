from pathlib import Path

p = Path("src/dairyos/api/farm_data_entry.py")
lines = p.read_text(encoding="utf-8").splitlines()

print("=== LINES 1175 to 1235 IN farm_data_entry.py ===")
for i in range(1175, min(len(lines), 1235)):
    print(f"{i+1:4d}: {lines[i]}")