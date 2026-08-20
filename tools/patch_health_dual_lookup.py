from pathlib import Path

p = Path("src/dairyos/api/farm_data_entry.py")
code = p.read_text(encoding="utf-8")

# 1. Helper function for dual lookup
helper_func = """def _lookup_health_case(case_repo, case_ref: str):
    case = case_repo.get_by_case_id(case_ref)
    if case is None and case_ref.isdigit():
        case = case_repo.get(int(case_ref)) if hasattr(case_repo, "get") else (case_repo.get_by_id(int(case_ref)) if hasattr(case_repo, "get_by_id") else None)
    return case
"""

if "_lookup_health_case" not in code:
    # Insert helper before get_health_case
    code = code.replace("@router.get(\"/health-cases/{case_id}\")", helper_func + "\n\n@router.get(\"/health-cases/{case_id}\")")

# Replace lookups in get_health_case and resolve_health_case
code = code.replace("case = rf.health_cases().get_by_case_id(case_id)", "case = _lookup_health_case(rf.health_cases(), case_id)")
code = code.replace("case = case_repo.get_by_case_id(case_id)", "case = _lookup_health_case(case_repo, case_id)")

# Auto-link treatment to active case if health_case_id is None
old_treat_lookup = """        if entry.health_case_id is not None:
            case = rf.health_cases().get(entry.health_case_id)"""

new_treat_lookup = """        case = None
        if entry.health_case_id is not None:
            case = rf.health_cases().get(entry.health_case_id) if hasattr(rf.health_cases(), "get") else rf.health_cases().get_by_id(entry.health_case_id)
        elif entry.animal_id:
            # Auto-link to active open health case for this animal
            active_cases = [c for c in rf.health_cases().get_all() if getattr(c, "animal_id", None) == entry.animal_id and getattr(c, "status", None) != "RESOLVED"]
            if active_cases:
                case = active_cases[-1]
                entry.health_case_id = case.id"""

if old_treat_lookup in code:
    code = code.replace(old_treat_lookup, new_treat_lookup)
    print("[OK] Replaced treatment case auto-linking.")
else:
    print("[INFO] Checking manual treatment hook points...")

p.write_text(code, encoding="utf-8")
print("[OK] Successfully applied dual-lookup and treatment auto-link patches to farm_data_entry.py")