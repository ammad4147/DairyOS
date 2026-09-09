from pathlib import Path
from types import SimpleNamespace as N
from datetime import UTC, datetime
from decimal import Decimal

from dairyos.finance.profitability.services.cost_of_production_service import CostOfProductionService

ROOT = Path(__file__).resolve().parents[2]

def _new_animal(client, tag):
    response = client.post('/farm/animals', json={'animal_type':'COW','breed':'Sahiwal','lifecycle_status':'LACTATING','is_currently_milking':True,'milking_frequency':'THRICE_DAILY','ear_tag':tag})
    assert response.status_code == 200, response.text
    return response.json()['animal_id']

def test_withdrawal_milk_remains_in_cost_denominator():
    now = datetime(2026, 9, 9, 12, tzinfo=UTC)
    milk = [N(total_yield=100, production_date=now, status='RECORDED'), N(total_yield=20, production_date=now, status='WITHDRAWAL')]
    finance = [N(amount=Decimal('12000'), transaction_date=now, transaction_type='EXPENSE', category='FEED', status='RECORDED')]
    result = CostOfProductionService().evaluate(milk, finance, days=1, now=now)
    assert result['milk_litres'] == 120
    assert result['cost_per_litre'] == 100

def test_cross_animal_observation_case_link_is_rejected(client, registered_animal):
    other = _new_animal(client, 'CASE-LINK-OTHER')
    case = client.post('/farm/health-cases', json={'animal_id':registered_animal,'severity':'MODERATE','diagnosis':'Audit'}).json()
    response = client.post('/farm/health-observations', json={'animal_id':other,'observation':'Audit','health_case_id':case['id']})
    assert response.status_code == 409

def test_cross_animal_treatment_case_link_is_rejected(client, registered_animal):
    other = _new_animal(client, 'CASE-TREAT-OTHER')
    case = client.post('/farm/health-cases', json={'animal_id':registered_animal,'severity':'MODERATE','diagnosis':'Audit'}).json()
    response = client.post('/farm/treatments', json={'animal_id':other,'medicine':'AuditDrug','milk_withdrawal_days':1,'health_case_id':case['id']})
    assert response.status_code == 409

def test_multiple_open_cases_require_explicit_treatment_case(client, registered_animal):
    for diagnosis in ('A','B'):
        response = client.post('/farm/health-cases', json={'animal_id':registered_animal,'severity':'MODERATE','diagnosis':diagnosis})
        assert response.status_code == 200
    response = client.post('/farm/treatments', json={'animal_id':registered_animal,'medicine':'AuditDrug','milk_withdrawal_days':1})
    assert response.status_code == 409
    assert 'will not guess' in response.json()['detail']

def test_feed_and_finance_reject_nonpositive_or_nonfinite(client):
    for value in (0, -1, 'NaN', 'Infinity', '-Infinity'):
        assert client.post('/farm/feed', json={'feed_type':'Audit','quantity_kg':value}).status_code == 422
        assert client.post('/farm/financial', json={'transaction_type':'EXPENSE','amount':value,'category':'FEED'}).status_code == 422

def test_unknown_finance_transaction_type_is_rejected(client):
    assert client.post('/farm/financial', json={'transaction_type':'EXPENES','amount':1000,'category':'FEED'}).status_code == 422

def test_fail_closed_and_historical_authority_contracts():
    coml = (ROOT/'src/dairyos/api/coml.py').read_text(encoding='utf-8')
    tmr = (ROOT/'src/dairyos/api/tmr.py').read_text(encoding='utf-8')
    feed = (ROOT/'src/dairyos/data/repositories/feed_record_repository.py').read_text(encoding='utf-8')
    assert 'FINANCE_OPEX_ATTRIBUTION_FAILED' in coml and 'status_code=503' in coml
    assert 'DAILY_COST_SNAPSHOT_GROUP = "TMR_DAILY_COST_SNAPSHOT"' in tmr
    assert 'basis = "LOCKED_DAILY_TMR"' in tmr
    assert 'basis = "DAILY_TMR_SNAPSHOT_MISSING"' in tmr

    period_block = tmr[
        tmr.index("def tmr_feed_cost_for_period("):
        tmr.index('@router.get("")')
    ]

    assert "WEEKLY_VET_ENDORSED_TMR" not in period_block
    assert "_endorsement_snapshots(" not in period_block
    assert 'basis = "LIVE_TMR"' not in period_block
    assert "UNENDORSED_LIVE_TMR_FALLBACK" not in period_block
    assert 'Feed operational date authority is unavailable' in feed
