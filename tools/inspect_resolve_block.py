from pathlib import Path

for p in Path("src/dairyos").rglob("*.py"):
    try:
        txt = p.read_text(encoding="utf-8")
        if "No health case" in txt:
            lines = txt.splitlines()
            print(f"=== File: {p} ===")
            for i, line in enumerate(lines, start=1):
                if "No health case" in line:
                    start = max(0, i - 20)
                    end = min(len(lines), i + 25)
                    for j in range(start, end):
                        print(f"{j+1:3d}: {lines[j]}")
    except Exception:
        pass