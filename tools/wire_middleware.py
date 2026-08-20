from pathlib import Path

app_path = Path("src/dairyos/app.py")
content = app_path.read_text(encoding="utf-8")

import_line = "from dairyos.middleware.enum_normalizer import PayloadNormalizationMiddleware"
middleware_line = "app.add_middleware(PayloadNormalizationMiddleware)"

if import_line not in content:
    lines = content.splitlines()
    # Insert import after the initial imports
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_idx = i + 1
    lines.insert(insert_idx, import_line)
    
    # Insert middleware call right after app = FastAPI(...)
    for i, line in enumerate(lines):
        if "app = FastAPI(" in line or "app =" in line and "FastAPI" in line:
            lines.insert(i + 1, f"\n{middleware_line}\n")
            break
            
    app_path.write_text("\n".join(lines), encoding="utf-8")
    print("[OK] Wired PayloadNormalizationMiddleware into src/dairyos/app.py")
else:
    print("[INFO] PayloadNormalizationMiddleware already registered in src/dairyos/app.py")