from dairyos.milk.intelligence.milk_alert_service import MilkAlertService


def test_completed_dates_exclude_incomplete_days_and_use_explicit_dates():
    service = MilkAlertService()
    records = {
        "2026-08-10": {"is_completed": True},
        "2026-08-11": {"is_completed": False, "session_count": 1},
        "2026-08-12": {"session_count": 2},
    }
    assert service.determine_completed_dates(records, expected_sessions_per_day=2) == [
        "2026-08-10",
        "2026-08-12",
    ]
    assert service.immediately_preceding_completed_date(
        "2026-08-12", ["2026-08-10", "2026-08-12"]
    ) == "2026-08-10"


def test_animal_threshold_boundaries_are_green_amber_and_red():
    service = MilkAlertService()

    none = service.compare_animal_yield(
        "A0", 85.1, 100, "2026-08-12", "2026-08-10"
    )
    amber_at_15 = service.compare_animal_yield(
        "A1", 85.0, 100, "2026-08-12", "2026-08-10"
    )
    amber_at_20 = service.compare_animal_yield(
        "A2", 80.0, 100, "2026-08-12", "2026-08-10"
    )
    red_above_20 = service.compare_animal_yield(
        "A3", 79.9, 100, "2026-08-12", "2026-08-10"
    )
    red_at_30 = service.compare_animal_yield(
        "A4", 70.0, 100, "2026-08-12", "2026-08-10"
    )

    assert none is None
    assert amber_at_15["severity"] == "AMBER"
    assert amber_at_15["drop_percent"] == 15.0
    assert amber_at_20["severity"] == "AMBER"
    assert amber_at_20["drop_percent"] == 20.0
    assert red_above_20["severity"] == "RED"
    assert red_above_20["drop_percent"] == 20.1
    assert red_at_30["severity"] == "RED"
    assert red_at_30["drop_percent"] == 30.0


def test_zero_baseline_does_not_create_false_drop_on_increase():
    service = MilkAlertService()
    assert service.compare_animal_yield("A1", 10, 0, "2026-08-12", "2026-08-10") is None
    assert service.compare_animal_yield("A1", 0, 0, "2026-08-12", "2026-08-10") is None


def test_herd_comparison_uses_same_thresholds():
    service = MilkAlertService()
    result = service.evaluate_herd_comparison("2026-08-12", "2026-08-10", 140, 200)
    assert result["alert"] == "HERD_YIELD_COMPARISON"
    assert result["drop_percent"] == 30.0
    assert result["severity"] == "RED"


def test_missed_session_contract_and_notification_badge():
    service = MilkAlertService()
    missed = service.missed_session_alert("A1", "2026-08-12", "evening")
    amber = service.compare_animal_yield("A2", 80, 100, "2026-08-12", "2026-08-10")
    badge = service.notification_badge([amber, missed])
    assert missed["alert"] == "MISSED_MILKING_SESSION"
    assert missed["date"] == "2026-08-12"
    assert badge["animal_yield_drop_count"] == 1
    assert badge["amber_animal_count"] == 1
    assert badge["missed_milking_session_count"] == 1
    assert badge["has_critical"] is True
    assert badge["total"] == 2
