# -*- coding: utf-8 -*-
from pathlib import Path
import re

files_to_check = list(Path("src/dairyos").rglob("*production_summary*.py")) + list(Path("src/dairyos").rglob("*farm_data_entry*.py"))

for p in files_to_check:
    txt = p.read_text(encoding="utf-8")
    modified = False
    
    # Clean up standard float roundings in summary dictionaries
    # Ensures values passed to response models round cleanly to whole numbers where appropriate
    if "total_production_liters" in txt or "total_yield" in txt:
        print(f"Checking {p.relative_to(Path('src/dairyos'))}...")