from pathlib import Path

app_path = Path("src/dairyos/app.py")
content = app_path.read_text(encoding="utf-8")

# Remove any existing mislocated references
content = content.replace("from dairyos.middleware.enum_normalizer import PayloadNormalizationMiddleware\n", "")
content = content.replace("from dairyos.middleware.enum_normalizer import PayloadNormalizationMiddleware", "")
content = content.replace("app.add_middleware(PayloadNormalizationMiddleware)\n", "")
content = content.replace("app.add_middleware(PayloadNormalizationMiddleware)", "")

lines = content.splitlines()

# 1. Insert import right at top
import_stmt = "from dairyos.middleware.enum_normalizer import PayloadNormalizationMiddleware"
lines.insert(0, import_stmt)

# 2. Insert middleware right after FastAPI instantiation
for i, line in enumerate(lines):
    if "app = FastAPI(" in line or (line.strip().startswith("app =") and "FastAPI" in line):
        lines.insert(i + 1, "app.add_middleware(PayloadNormalizationMiddleware)")
        break

app_path.write_text("\n".join(lines), encoding="utf-8")
print("[OK] Successfully reordered imports and middleware registration in src/dairyos/app.py")