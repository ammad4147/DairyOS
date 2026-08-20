from pathlib import Path

p = Path("src/dairyos/api/farm_data_entry.py")
content = p.read_text(encoding="utf-8")

# Pattern matching treatment persistence
target_marker = "treatment = Treatment("
if target_marker in content:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "treatment = Treatment(" in line:
            # Insert auto-linking logic right before treatment instantiation
            injection = [
                "        # Auto-link treatment to active open health case if omitted",
                "        resolved_case_id = getattr(entry, 'health_case_id', None)",
                "        if resolved_case_id is None and entry.animal_id:",
                "            try:",
                "                open_cases = [c for c in rf.health_cases().get_all() if getattr(c, 'animal_id', None) == entry.animal_id and getattr(c, 'status', None) != 'RESOLVED']",
                "                if open_cases:",
                "                    resolved_case_id = open_cases[-1].id",
                "            except Exception:",
                "                pass",
            ]
            lines.insert(i, "\n".join(injection))
            break

    # Replace health_case_id assignment in Treatment instantiation
    new_code = "\n".join(lines).replace("health_case_id=entry.health_case_id", "health_case_id=resolved_case_id")
    p.write_text(new_code, encoding="utf-8")
    print("[OK] Successfully injected treatment auto-linking logic.")
else:
    print("[WARN] Target marker not found, check lines manually.")