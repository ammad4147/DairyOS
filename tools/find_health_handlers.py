from pathlib import Path

for p in Path("src/dairyos").rglob("*.py"):
    try:
        txt = p.read_text(encoding="utf-8")
        if "No health case" in txt or "/health-cases/{case_id}/resolve" in txt:
            print(f"\n=== Case Resolve Handler in: {p} ===")
            for i, line in enumerate(txt.splitlines(), start=1):
                if "No health case" in line or "def resolve" in line:
                    print(f"  {i:3d}: {line}")
        if "/treatments" in txt and ("@router.post" in txt or "@app.post" in txt):
            print(f"\n=== Treatment Post Handler in: {p} ===")
            for i, line in enumerate(txt.splitlines(), start=1):
                if "treatments" in line and ("post" in line or "def " in line):
                    print(f"  {i:3d}: {line}")
    except Exception:
        pass