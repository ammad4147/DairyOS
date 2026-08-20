from pathlib import Path

p = Path("src/dairyos/api/farm_data_entry.py")
code = p.read_text(encoding="utf-8")

old_block = """        linked_case = None
        if entry.health_case_id is not None:
            case_repo = rf.health_cases()
            linked_case = case_repo.get_by_id(entry.health_case_id)
            if linked_case is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"health_case_id {entry.health_case_id} does not exist.",
                )"""

new_block = """        linked_case = None
        case_repo = rf.health_cases()
        if entry.health_case_id is not None:
            linked_case = case_repo.get_by_id(entry.health_case_id)
            if linked_case is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"health_case_id {entry.health_case_id} does not exist.",
                )
        elif entry.animal_id:
            open_cases = [
                c for c in case_repo.get_all()
                if getattr(c, "animal_id", None) == entry.animal_id
                and getattr(c, "status", None) != "RESOLVED"
            ]
            if open_cases:
                linked_case = open_cases[-1]
                entry.health_case_id = linked_case.id"""

if old_block in code:
    code = code.replace(old_block, new_block)
    p.write_text(code, encoding="utf-8")
    print("[OK] Successfully patched treatment auto-linking logic.")
else:
    print("[WARN] Exact match failed; printing lines around 1177...")