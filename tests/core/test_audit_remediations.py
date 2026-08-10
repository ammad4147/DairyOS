from datetime import datetime, timedelta, timezone, date
import pytest

from dairyos.operations.intelligence.services.withdrawal_service import (
    WithdrawalService,
    WithdrawalPeriod,
)
from dairyos.milk.services.milk_production_intelligence_service import (
    MilkProductionIntelligenceService,
)
from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)
from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)
from dairyos.data.models.animal import Animal
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.feed.intelligence.models.feed_cost_metric import FeedCostMetric
from dairyos.herd.reproduction.services.reproduction_kpi_service import (
    ReproductionKpiService,
)
from dairyos.herd.calves.services.calf_management_service import (
    CalfManagementService,
)
from dairyos.farm.intelligence.production.services.production_efficiency_service import (
    ProductionEfficiencyService,
)
from dairyos.herd.services.cow_lifetime_performance_service import (
    CowLifetimePerformanceService,
)
from dairyos.milk.services.milk_traceability_service import (
    MilkTraceabilityService,
)
from dairyos.alerts.services.yield_drop_alert_service import (
    YieldDropAlertService,
)
from dairyos.api.animal_management.router import serialize_animal


def test_withdrawal_service_correct_logic():
    now = datetime.now(timezone.utc)
    service = WithdrawalService()

    # Active treatment window: start 1 hour ago, end in 2 days
    active_period = WithdrawalPeriod(
        treatment_id="TR-1001",
        animal_id="COW-101",
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(days=2),
    )
    service.add_period(active_period)

    # Expired treatment window: start 5 days ago, ended 2 days ago
    expired_period = WithdrawalPeriod(
        treatment_id="TR-1002",
        animal_id="COW-102",
        start_time=now - timedelta(days=5),
        end_time=now - timedelta(days=2),
    )
    service.add_period(expired_period)

    # Active cow MUST evaluate as withdrawn (unsafe to milk)
    assert service.is_withdrawn("TR-1001", at=now) is True
    assert service.is_animal_withdrawn("COW-101", at=now) is True

    # Expired cow MUST evaluate as safe (not withdrawn)
    assert service.is_withdrawn("TR-1002", at=now) is False
    assert service.is_animal_withdrawn("COW-102", at=now) is False


def test_unique_animal_milk_yield_calculation():
    state_service = FarmOperationalStateService()
    state = state_service.get_state()

    # Record morning shift milk entries for 2 cows
    state.record_milk_activity("MORNING", 15.0, operator="Worker1", animal_id="COW-01")
    state.record_milk_activity("MORNING", 20.0, operator="Worker1", animal_id="COW-02")
    # Duplicate record for COW-01 in morning shift should not inflate cow count
    state.record_milk_activity("MORNING", 5.0, operator="Worker1", animal_id="COW-01")

    # Record evening shift milk entries for the SAME 2 cows
    state.record_milk_activity("EVENING", 12.0, operator="Worker2", animal_id="COW-01")
    state.record_milk_activity("EVENING", 18.0, operator="Worker2", animal_id="COW-02")

    intel_service = MilkProductionIntelligenceService(state_service)
    
    # Total litres: 15 + 20 + 5 + 12 + 18 = 70L
    # Unique animals: 2 (COW-01, COW-02)
    # Average yield per cow MUST be 70 / 2 = 35.0L
    avg_yield = intel_service.litres_per_animal()
    assert avg_yield == 35.0


def test_animal_lineage_and_serialization():
    animal = Animal(
        animal_id="COW-500",
        animal_type="COW",
        breed="Holstein",
        sex="FEMALE",
        dam_id="COW-200",
        sire_id="BULL-01",
    )
    assert animal.dam_id == "COW-200"
    assert animal.sire_id == "BULL-01"

    serialized = serialize_animal(animal)
    assert serialized["dam_id"] == "COW-200"
    assert serialized["sire_id"] == "BULL-01"


def test_financial_transaction_linkage_and_pkr_currency():
    tx = FinancialTransaction(
        transaction_type="INCOME",
        category="MILK_SALE",
        amount=45000.0,
        currency="PKR",
        animal_id="COW-101",
        milk_sale_id="SALE-2026-08",
    )
    assert tx.currency == "PKR"
    assert tx.animal_id == "COW-101"
    assert tx.milk_sale_id == "SALE-2026-08"


def test_feed_cost_metric_formulas():
    metric = FeedCostMetric(
        animal_group="LACTATING",
        feed_cost=50000.0,
        milk_revenue=200000.0,
        feed_quantity_kg=250.0,
        milk_litres=200.0,
    )

    # Revenue share: 50,000 / 200,000 = 0.25 (25%)
    assert metric.feed_cost_revenue_share == 0.25
    assert metric.feed_cost_ratio == 0.25

    # True FCR: 250kg feed / 200L milk = 1.25 kg/L
    assert metric.feed_conversion_ratio == 1.25


def test_reproduction_kpi_service():
    svc = ReproductionKpiService()
    
    ci = svc.calculate_calving_interval(date(2025, 1, 1), date(2026, 1, 15))
    assert ci == 379

    days_open = svc.calculate_days_open(date(2025, 1, 1), date(2025, 3, 20))
    assert days_open == 78

    cr = svc.calculate_conception_rate(3, 5)
    assert cr == 60.0

    spc = svc.calculate_services_per_conception(5, 3)
    assert spc == 1.67


def test_calf_adg_calculation():
    svc = CalfManagementService()
    adg = svc.calculate_adg(birth_weight_kg=35.0, current_weight_kg=80.0, age_days=60)
    # (80 - 35) / 60 = 45 / 60 = 0.75 kg/day
    assert adg == 0.75


def test_production_efficiency_pkr_service():
    svc = ProductionEfficiencyService(currency="PKR", feed_cost_threshold_per_litre=100.0)
    eval_result = svc.evaluate(milk_litres=500.0, milking_animals=20, feed_cost=45000.0)
    
    # 45000 / 500 = PKR 90/L <= 100 threshold => normal
    assert eval_result.feed_cost_per_litre == 90.0
    assert eval_result.efficiency_status == "normal"
    assert getattr(eval_result, "currency") == "PKR"


def test_cow_lifetime_performance_service():
    svc = CowLifetimePerformanceService(default_currency="PKR", milk_price_per_litre=220.0)
    summary = svc.evaluate_cow_lifetime(
        animal_id="COW-301",
        total_milk_litres=12000.0,
        feed_cost=1500000.0,
        health_cost=100000.0,
        current_lactation_days=150,
        current_lactation_yield=4500.0,
    )
    assert summary.currency == "PKR"
    # 12000 * 220 = 2,640,000 revenue
    assert summary.total_lifetime_revenue == 2640000.0
    # Net profit: 2,640,000 - 1,600,000 = 1,040,000 PKR
    assert summary.net_lifetime_profitability == 1040000.0
    assert summary.status == "PROFITABLE"
    assert summary.projected_305_day_yield_litres > 4500.0


def test_milk_traceability_service():
    svc = MilkTraceabilityService()
    svc.create_batch("BATCH-01", tank_id="TANK-A", shift="MORNING")
    
    svc.add_milking_to_batch("BATCH-01", animal_id="COW-101", litres=25.0)
    svc.add_milking_to_batch("BATCH-01", animal_id="COW-102", litres=30.0)

    batches = svc.trace_animal("COW-101")
    assert len(batches) == 1
    assert batches[0].total_litres == 55.0

    svc.dispatch_delivery("BATCH-01", delivery_ticket_id="TICKET-999")
    assert batches[0].status == "DISPATCHED"


def test_yield_drop_alert_service():
    svc = YieldDropAlertService(drop_threshold_pct=15.0)
    
    # 7-day baseline average: 30.0L
    recent_7_days = [30.0, 29.5, 30.5, 30.0, 31.0, 29.0, 30.0]
    
    # Current yield drops to 20.0L (33.3% drop)
    alert = svc.evaluate_cow_yield("COW-800", recent_7_days, current_yield_litres=20.0)
    assert alert is not None
    assert alert.severity == "CRITICAL"
    assert alert.drop_pct == 33.3
