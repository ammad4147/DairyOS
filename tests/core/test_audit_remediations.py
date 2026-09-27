from datetime import UTC, date, datetime, timedelta

from dairyos.api.animal_management.router import serialize_animal
from dairyos.data.models.animal import Animal
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)
from dairyos.herd.reproduction.services.reproduction_kpi_service import (
    ReproductionKpiService,
)
from dairyos.milk.services.milk_production_intelligence_service import (
    MilkProductionIntelligenceService,
)
from dairyos.operations.intelligence.services.withdrawal_service import (
    WithdrawalPeriod,
    WithdrawalService,
)


def test_withdrawal_service_correct_logic():
    now = datetime.now(UTC)
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
