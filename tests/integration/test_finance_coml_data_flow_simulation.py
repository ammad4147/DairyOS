"""Input-driven Finance, Payroll and COML simulations."""

from decimal import Decimal


def test_payroll_payment_reaches_finance_once(client):
    created = client.post(
        "/farm/payroll",
        json={
            "employee_name": "Simulation Worker",
            "employee_role": "Milker",
            "period_start": "2026-08-01",
            "period_end": "2026-08-31",
            "worked_days": "20",
            "base_pay": "40000",
            "overtime_hours": "10",
            "overtime_rate": "250",
            "allowances": "2000",
            "advances": "1000",
            "deductions": "500",
            "notes": "Input-driven simulation",
        },
    )
    assert created.status_code == 201, created.text
    payroll = created.json()
    assert Decimal(payroll["gross_pay"]) == Decimal("44500")
    assert Decimal(payroll["net_pay"]) == Decimal("43500")

    payment = client.post(
        f"/farm/payroll/{payroll['id']}/pay",
        params={"payment_date": "2026-08-31"},
    )
    assert payment.status_code == 200, payment.text
    paid = payment.json()
    assert paid["status"] == "PAID"
    assert paid["finance_transaction_id"] is not None

    repeat = client.post(
        f"/farm/payroll/{payroll['id']}/pay",
        params={"payment_date": "2026-08-31"},
    )
    assert repeat.status_code == 200, repeat.text
    assert repeat.json()["finance_transaction_id"] == paid["finance_transaction_id"]

    finance = client.get("/farm/financial")
    assert finance.status_code == 200, finance.text
    records = finance.json()
    payroll_rows = [
        row
        for row in records
        if row.get("reference") == f"PAYROLL#{payroll['id']}"
    ]
    assert len(payroll_rows) == 1, payroll_rows
    assert float(payroll_rows[0]["amount"]) == 43500.0
    assert payroll_rows[0]["payroll_record_id"] == payroll["id"]


def test_coml_uses_only_supplied_period_inputs_and_rates(client):
    response = client.post(
        "/farm/coml/calculate",
        json={
            "period_start": "2026-08-01",
            "period_end": "2026-08-31",
            "milk_produced_liters": "10000",
            "feed_items": [
                {"item": "Silage", "quantity": "5000", "unit": "kg", "unit_rate": "12"},
                {"item": "Concentrate", "quantity": "2000", "unit": "kg", "unit_rate": "30"},
            ],
            "operating_items": [
                {"item": "Electricity", "quantity": "1", "unit": "month", "unit_rate": "25000"},
                {"item": "Labour", "quantity": "1", "unit": "month", "unit_rate": "40000"},
            ],
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["data_status"] == "CALCULATED_MANUAL_INPUT"
    assert result["period_days"] == 31
    assert Decimal(result["feed_total"]) == Decimal("120000")
    assert Decimal(result["operating_total"]) == Decimal("65000")
    assert Decimal(result["total_coml_per_liter"]) == Decimal("18.5")

    changed = client.post(
        "/farm/coml/calculate",
        json={
            "period_start": "2026-08-01",
            "period_end": "2026-08-31",
            "milk_produced_liters": "12500",
            "feed_items": [
                {"item": "Silage", "quantity": "5000", "unit": "kg", "unit_rate": "12"},
                {"item": "Concentrate", "quantity": "2000", "unit": "kg", "unit_rate": "30"},
            ],
            "operating_items": [
                {"item": "Electricity", "quantity": "1", "unit": "month", "unit_rate": "25000"},
                {"item": "Labour", "quantity": "1", "unit": "month", "unit_rate": "40000"},
            ],
        },
    )
    assert changed.status_code == 200, changed.text
    changed_result = changed.json()
    assert Decimal(changed_result["total_coml_per_liter"]) == Decimal("14.8")
    assert changed_result["period_days"] == 31
