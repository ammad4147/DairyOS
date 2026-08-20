from pathlib import Path

p = Path("src/dairyos/api/farm_data_entry.py")
lines = p.read_text(encoding="utf-8").splitlines()

print("=== LINES 1115 to 1185 IN farm_data_entry.py ===")
for i in range(1115, min(len(lines), 1185)):
    print(f"{i+1:4d}: {lines[i]}")