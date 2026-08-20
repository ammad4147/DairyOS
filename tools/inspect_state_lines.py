from pathlib import Path

target_file = Path("src/dairyos/farm/operations/state/farm_operational_state.py")
lines = target_file.read_text(encoding="utf-8").splitlines()

print("=== LINES 170-205 IN farm_operational_state.py ===")
for i, line in enumerate(lines[169:205], start=170):
    print(f"{i:3d}: {line}")