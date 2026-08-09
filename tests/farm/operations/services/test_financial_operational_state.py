from dairyos.farm.operations.models.farm_operation_event import (
    FarmOperationEvent,
)

from dairyos.farm.operations.state.farm_operational_state_service import (
    FarmOperationalStateService,
)

from dairyos.farm.operations.services.financial_intelligence_service import (
    FinancialIntelligenceService,
)


def test_financial_status_event_updates_operational_state():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(
        event_type="financial_status_recorded",
        animal_id=None,
        operator="manager",
        payload={
            "financial_type": "cash_position",
            "details": {
                "cash_available": 5000000,
                "minimum_cash_required": 1000000,
                "awareness_status": "READY",
            },
        },
    )


    state = service.process_event(event)


    assert (
        state.financial_status["cash_position"]
        ["cash_available"]
        ==
        5000000
    )



def test_expense_event_updates_financial_state():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(
        event_type="expense_recorded",
        animal_id=None,
        operator="manager",
        payload={
            "financial_type": "feed_expense",
            "details": {
                "amount": 75000,
                "category": "feed",
            },
        },
    )


    state = service.process_event(event)


    assert (
        state.financial_status["feed_expense"]
        ["amount"]
        ==
        75000
    )



def test_revenue_event_updates_financial_state():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(
        event_type="revenue_recorded",
        animal_id=None,
        operator="manager",
        payload={
            "financial_type": "milk_revenue",
            "details": {
                "amount": 250000,
                "source": "milk_sales",
            },
        },
    )


    state = service.process_event(event)


    assert (
        state.financial_status["milk_revenue"]
        ["amount"]
        ==
        250000
    )



def test_financial_intelligence_detects_cash_reserve_risk():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(
        event_type="cash_position_recorded",
        animal_id=None,
        operator="manager",
        payload={
            "financial_type": "cash_position",
            "details": {
                "cash_available": 500000,
                "minimum_cash_required": 1000000,
            },
        },
    )


    state = service.process_event(event)


    decisions = (
        FinancialIntelligenceService()
        .evaluate(state)
    )


    assert any(
        decision["action"]
        ==
        "review_cash_reserve"
        for decision in decisions
    )



def test_financial_intelligence_detects_warning_status():

    service = FarmOperationalStateService()


    event = FarmOperationEvent(
        event_type="financial_transaction_recorded",
        animal_id=None,
        operator="manager",
        payload={
            "financial_type": "monthly_position",
            "details": {
                "awareness_status": "WARNING",
            },
        },
    )


    state = service.process_event(event)


    decisions = (
        FinancialIntelligenceService()
        .evaluate(state)
    )


    assert any(
        decision["action"]
        ==
        "review_financial_position"
        for decision in decisions
    )



def test_financial_visibility_missing():

    service = FarmOperationalStateService()


    state = service.get_state()


    decisions = (
        FinancialIntelligenceService()
        .evaluate(state)
    )


    assert any(
        decision["action"]
        ==
        "record_financial_activity"
        for decision in decisions
    )
