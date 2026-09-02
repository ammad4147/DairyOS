from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MILK=ROOT/'src'/'DairyOS.Web'/'src'/'components'/'MilkTab.tsx'; PASSPORT=ROOT/'tests'/'api'/'test_animal_passport.py'; SESSION=ROOT/'tests'/'milk'/'test_animal_session_authority_remediation.py'
def t(p): return p.read_text(encoding='utf-8-sig')
def test_register_contract():
    s=t(MILK); assert 'Daily Milk Register' in s; assert 'Animal ID' in s; assert 'ID &amp; Type' not in s; assert 'Sessions Production' in s; assert 'Total Production' in s; assert ".filter((entry) => entry.kind === 'PRODUCTION')" in s; assert "`${productions.length} production records`" in s; assert "TODAY'S MILKING SESSIONS ALREADY RECORDED" in s
def test_passport_click_and_width():
    s=t(MILK); assert "onOpenAnimalPassport((entry.row as ProductionRow).animal_id)" in s; assert 'minWidth: 760' not in s; assert "gridTemplateColumns:\n                'minmax(0,1fr) minmax(260px,.5fr)'" not in s
def test_calf_lineage_contract():
    s=t(PASSPORT); assert 'dam_id=dam' in s; assert 'data["lineage"]["descendants"]' in s; assert 'data["history"]["lineage_descendants"]' in s
def test_session_authority_contract():
    s=t(SESSION); assert 'test_other_animals_do_not_advance_td002_session' in s; assert 'test_twice_daily_rejects_afternoon_and_duplicate' in s; assert 'test_thrice_daily_accepts_exactly_three_sessions' in s; assert 'test_voided_day_reopens_authorized_sessions' in s
