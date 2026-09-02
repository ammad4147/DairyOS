from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")

def test_voided_milk_row_is_not_reactivated_in_place():
    source = read("src/dairyos/data/repositories/milk_production_repository.py")
    assert 'existing.status = "RECORDED"' not in source
    assert "existing.session_ledger = False" in source
    assert "return self.add(production)" in source

def test_void_releases_governed_slot_but_preserves_audit_row():
    source = read("src/dairyos/api/milk_traceability.py")
    block = source[source.index("def void_milk_production"):source.index('@router.post("/dispositions")')]
    assert "record.session_ledger = False" in block
    assert 'record.status = "VOID"' in block
    assert "_append_void_note" in block

def test_passport_core_does_not_depend_on_ancillary_fetches():
    source = read("src/DairyOS.Web/src/components/AnimalPassportModal.tsx")
    assert "const [a,p]=await Promise.all" in source
    assert "const safeFetch=async(url:string)" in source
    assert "setPassport(await p.json())" in source
    assert "const [a,p,d,h,t,v]=await Promise.all" not in source
