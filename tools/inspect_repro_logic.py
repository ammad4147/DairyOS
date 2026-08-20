from pathlib import Path

# Search for reproduction overview / confirmed pregnancies logic
src_dir = Path("src/dairyos")
matches = list(src_dir.rglob("*reproduction*.py")) + list(src_dir.rglob("*breeding*.py"))

for p in matches:
    content = p.read_text(encoding="utf-8")
    if "confirmed_pregnancies" in content:
        print(f"\n=== Found logic in: {p} ===")
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if any(k in line for k in ["confirmed_pregnancies", "conception_rate", "PREGNANCY_CHECK"]):
                start = max(1, i - 2)
                end = min(len(lines), i + 6)
                print(f"--- Around Line {i} ---")
                for j in range(start, end):
                    print(f"{j:3d}: {lines[j-1]}")
                break