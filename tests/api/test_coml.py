from datetime import date


def test_coml_month_lock_and_update(client):
    month = "2026-08-01"

    first = client.post(
        "/farm/coml/lock",
        json={
            "month_start": month,
            "feed_cost_per_liter": 18.5,
            "opex_cost_per_liter": 6.5,
            "notes": "TMR basis + monthly OPEX management estimate",
            "updated_by": "test-user",
        },
    )
    assert first.status_code == 200
    payload = first.json()
    assert payload["has_official"] is True
    assert payload["record"]["month_label"] == "August 2026"
    assert payload["record"]["feed_cost_per_liter"] == 18.5
    assert payload["record"]["opex_cost_per_liter"] == 6.5
    assert payload["record"]["total_coml_per_liter"] == 25.0

    current = client.get(f"/farm/coml?month_start={month}")
    assert current.status_code == 200
    assert current.json()["record"]["total_coml_per_liter"] == 25.0
    assert current.json()["reminder_status"] == "LOCKED"

    updated = client.post(
        "/farm/coml/lock",
        json={
            "month_start": month,
            "feed_cost_per_liter": 19.0,
            "opex_cost_per_liter": 7.0,
            "notes": "Updated management estimate",
            "updated_by": "test-user",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["record"]["total_coml_per_liter"] == 26.0

    history = client.get("/farm/coml/history")
    assert history.status_code == 200
    rows = [row for row in history.json()["records"] if row["month_start"] == month]
    assert len(rows) == 1
    assert rows[0]["total_coml_per_liter"] == 26.0


def test_coml_requires_first_calendar_day(client):
    response = client.post(
        "/farm/coml/lock",
        json={
            "month_start": "2026-08-15",
            "feed_cost_per_liter": 18,
            "opex_cost_per_liter": 7,
        },
    )
    assert response.status_code == 422
    assert "first calendar day" in response.json()["detail"]


def test_coml_reminder_setting_is_persistent(client):
    response = client.put("/farm/coml/settings", json={"reminder_day": 3})
    assert response.status_code == 200
    assert response.json()["reminder_day"] == 3

    settings = client.get("/farm/coml/settings")
    assert settings.status_code == 200
    assert settings.json()["reminder_day"] == 3


def test_coml_missing_record_reports_due_for_current_month(client, monkeypatch):
    from dairyos.api import coml

    monkeypatch.setattr(coml.OperationalDateAuthority, "current_date", lambda self: date(2026, 8, 23))
    monkeypatch.setattr(coml, "DEFAULT_REMINDER_DAY", 1)
    response = client.get("/farm/coml?month_start=2026-08-01")
    assert response.status_code == 200
    body = response.json()
    assert body["has_official"] is False
    assert body["reminder_due"] is True
    assert body["reminder_status"] in {"DUE", "OVERDUE"}
