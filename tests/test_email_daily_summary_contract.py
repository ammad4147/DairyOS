from datetime import date

from dairyos.email.digest import DashboardDigestService


def _service():
    service = object.__new__(DashboardDigestService)
    service._dashboard = lambda: {"health": {"active_exceptions": 2}}
    service._milk_snapshot = lambda digest_date: {
        "total_yield": 90.0,
        "change_percent": -12.5,
        "sold": 70.0,
        "domestic_use": 5.0,
        "calf_feed": 10.0,
        "wastage": 5.0,
        "other": 0.0,
        "unaccounted": 0.0,
        "watchlist": [
            {
                "animal_id": "AN-001",
                "previous_litres": 20.0,
                "current_litres": 15.0,
                "drop_percentage": 25.0,
                "severity": "HIGH",
            }
        ],
    }
    service._herd_snapshot = lambda digest_date: {
        "total": 25,
        "counts": {
            "Milking": 10,
            "Dry": 4,
            "Heifer": 5,
            "Female Calf": 3,
            "Male Calf": 2,
            "Bull": 1,
        },
        "mortalities": [
            {
                "animal_id": "AN-099",
                "category": "Exited",
                "breed": "Holstein",
                "cause": "Recorded cause",
            }
        ],
    }
    service._financial_snapshot = lambda digest_date: {
        "revenue_received": 14000.0,
        "expenses": 5000.0,
    }
    service._active_warnings = lambda: ["Milk reconciliation exception"]
    return service


def test_daily_summary_contains_approved_operational_sections():
    subject, body = _service().render(
        digest_date=date(2026, 9, 6),
        user_permissions={"dashboard.view", "dashboard.view_finance"},
    )

    assert subject == "DairyOS Daily Summary — 2026-09-06"
    assert "Operational Date: 2026-09-06" in body
    assert "MILK PRODUCTION" in body
    assert "Total yield today: 90.0 litres" in body
    assert "Change vs previous recorded day: -12.5%" in body
    assert "Milk Sold: 70.0 litres" in body
    assert "Domestic Use: 5.0 litres" in body
    assert "Calves Feed: 10.0 litres" in body
    assert "Wastage: 5.0 litres" in body
    assert "Unaccounted Milk: 0.0 litres" in body
    assert "YIELD DROP WATCHLIST" in body
    assert "AN-001: 20.0 L → 15.0 L; drop 25.0%; severity HIGH" in body
    assert "HERD STATUS" in body
    assert "Total headcount: 25" in body
    assert "Milking: 10" in body
    assert "Dry: 4" in body
    assert "Heifers: 5" in body
    assert "Female Calves: 3" in body
    assert "Male Calves: 2" in body
    assert "Bulls: 1" in body
    assert "Active health Alerts: 2" in body
    assert "Any Mortalities? Yes" in body
    assert "Animal ID: AN-099" in body
    assert "FINANCIAL SNAPSHOT" in body
    assert "Revenue Received today: PKR 14,000.00" in body
    assert "Expenses today: PKR 5,000.00" in body
    assert "ACTIVE WARNINGS" in body
    assert "- Milk reconciliation exception" in body


def test_daily_summary_hides_finance_without_finance_permission():
    _, body = _service().render(
        digest_date=date(2026, 9, 6),
        user_permissions={"dashboard.view"},
    )
    assert "FINANCIAL SNAPSHOT" not in body


def test_daily_summary_has_explicit_empty_states():
    service = _service()
    service._milk_snapshot = lambda digest_date: {
        "total_yield": 0.0,
        "change_percent": None,
        "sold": 0.0,
        "domestic_use": 0.0,
        "calf_feed": 0.0,
        "wastage": 0.0,
        "other": 0.0,
        "unaccounted": 0.0,
        "watchlist": [],
    }
    service._herd_snapshot = lambda digest_date: {
        "total": 0,
        "counts": {
            "Milking": 0,
            "Dry": 0,
            "Heifer": 0,
            "Female Calf": 0,
            "Male Calf": 0,
            "Bull": 0,
        },
        "mortalities": [],
    }
    service._active_warnings = lambda: []

    _, body = service.render(
        digest_date=date(2026, 9, 6),
        user_permissions={"dashboard.view"},
    )

    assert "No animals on the Yield Drop Watchlist." in body
    assert "Any Mortalities? No" in body
    assert "No active operational warnings." in body
