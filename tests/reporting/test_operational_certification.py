"""Deterministic certification of the Herd, Milk, Feed, Breeding, Health,
Cost of Milk and Management reports against the synthetic farm."""

from __future__ import annotations

from decimal import Decimal

from tests.reporting.conftest import metric, section
from tests.reporting.synthetic_farm import DAILY_MILK, EXPECTED, HERD

D = Decimal
SEPTEMBER = {"mode": "MONTH", "year": 2026, "month": 9}
CUSTOM = {"mode": "CUSTOM", "start_date": "2026-08-10", "end_date": "2026-09-17"}


# ------------------------------------------------------------------ herd
def test_herd_totals_and_individual_membership(run):
    summary = run("herd-by-category")
    assert metric(summary, "herd") == EXPECTED["herd"]["total"] == 48
    for category, ids in HERD.items():
        assert metric(summary, category) == len(ids)
        body = run(f"herd-{category.lower().replace(' ', '-')}")
        listed = {r["animal_id"] for r in section(body, "register")["rows"]}
        assert listed == set(ids), f"{category} membership differs"
    assert all(c["status"] == "PASS" for c in summary["reconciliation"])  # agrees with Dashboard


def test_herd_agrees_with_dashboard(farm, run):
    dashboard = farm.get("/dashboard").json()
    composition = dashboard["animals"]["composition"]
    assert dashboard["animals"]["total"] == 48
    counts = {item["name"]: item["value"] for item in composition}
    assert counts == {k: v for k, v in EXPECTED["herd"].items() if k != "total"}


def test_exited_animals_never_appear_in_the_current_herd(run):
    register = run("herd-register")
    ids = {r["animal_id"] for r in section(register, "register")["rows"]}
    assert len(ids) == 48 and not ids & {"XS001", "XD001"}
    with_exits = run("herd-register", filters={"include_exited": True})
    statuses = {r["animal_id"]: r["status"] for r in section(with_exits, "register")["rows"]}
    assert (statuses["XS001"], statuses["XD001"]) == ("Sold", "Deceased")


def test_herd_register_default_columns_hide_the_schema(run):
    body = run("herd-milking", columns="default")
    keys = [c["key"] for c in section(body, "register")["columns"]]
    assert keys == ["animal_id", "ear_tag", "breed", "age", "production_group", "location", "milking_frequency"]
    labels = {c["label"] for c in section(body, "register")["columns"]}
    assert not labels & {"ID", "Created At", "Updated At", "Photo Data", "Lifecycle Status", "Active",
                         "Non Milking Directive", "Non Milking Changed By", "Legacy Animal ID"}


def test_herd_filters_and_breed_breakdown(run):
    body = run("herd-milking", filters={"production_group": "High Yield"})
    assert {r["animal_id"] for r in section(body, "register")["rows"]} == {f"M{i:03d}" for i in range(1, 11)}
    breeds = section(run("herd-by-category"), "breeds")
    assert breeds["totals"]["total"] == 48 and sum(r["total"] for r in breeds["rows"]) == 48


def test_exits_mortality_and_movement(run):
    exits = run("herd-exits-mortality", period=SEPTEMBER)
    rows = {r["animal_id"]: r for r in section(exits, "exits")["rows"]}
    assert rows["XD001"]["exit_type"] == "Deceased" and rows["XD001"]["cause"] == "Bloat"
    assert rows["XD001"]["exit_date"] == "2026-09-08"
    assert rows["XS001"]["exit_type"] == "Sold" and D(str(rows["XS001"]["amount"])) == D("150000")
    assert (metric(exits, "deaths"), metric(exits, "sold")) == (1, 1)
    assert metric(run("herd-exits-mortality", period=SEPTEMBER, filters={"exit_type": "DECEASED"}), "exits") == 1
    assert metric(run("herd-exits-mortality", period={"mode": "MONTH", "year": 2026, "month": 8}), "exits") == 0

    movement = run("herd-movement", period=SEPTEMBER)
    assert (metric(movement, "births"), metric(movement, "acquisitions"), metric(movement, "exits")) == (1, 1, 2)
    assert metric(movement, "net") == 0


def test_identification_gaps(run):
    body = run("herd-identification", filters={"only_gaps": True})
    rows = section(body, "identification")["rows"]
    assert rows and all(r["identification_gap"] for r in rows)
    assert metric(run("herd-identification"), "animals") == 48


# ------------------------------------------------------------------ milk
def test_milk_agrees_with_dashboard(farm, monkeypatch, run):
    """Milk <-> Dashboard: the Dashboard's day total equals the report's."""
    import datetime as _dt
    from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService
    from tests.reporting.synthetic_farm import PKT

    monkeypatch.setattr(FarmSettingsService, "get_operational_datetime",
                        lambda self: _dt.datetime(2026, 9, 17, 20, 0, tzinfo=PKT))
    dashboard = farm.get("/dashboard").json()
    report = run("milk-daily-production", period={"mode": "TODAY"})
    assert report["period"]["start_date"] == "2026-09-17"
    assert metric(report, "total") == 491.0
    herd_metrics = dashboard["animals"]["herd_metrics"]
    assert herd_metrics["average_yield_total_herd_liters"] == round(491.0 / 48, 2)


def test_daily_milk_by_session(run):
    body = run("milk-daily-production", period=SEPTEMBER)
    rows = section(body, "daily")["rows"]
    assert len(rows) == 17 and rows[0]["date"] == "2026-09-01" and rows[-1]["date"] == "2026-09-17"
    for row in rows:
        assert (row["morning"], row["afternoon"], row["evening"], row["total"]) == (
            DAILY_MILK["morning"], DAILY_MILK["afternoon"], DAILY_MILK["evening"], DAILY_MILK["total"])
        assert row["animals_milked"] == 20
    assert metric(body, "total") == EXPECTED["milk_sep"] == 8347.0
    assert all(c["status"] == "PASS" for c in body["reconciliation"])  # equals the COML denominator
    # VOID, NOT_MILKED and non-ledger rows on 16-Sep changed nothing.
    assert next(r for r in rows if r["date"] == "2026-09-16")["total"] == 491.0


def test_milk_operational_date_boundaries(run):
    assert metric(run("milk-daily-production", period=CUSTOM), "total") == EXPECTED["milk_custom"]
    one_day = run("milk-daily-production", period={"mode": "CUSTOM", "start_date": "2026-08-31", "end_date": "2026-08-31"})
    assert metric(one_day, "total") == 491.0
    assert metric(run("milk-daily-production", period={"mode": "CUSTOM", "start_date": "2026-08-30", "end_date": "2026-08-30"}), "days") == 0


def test_milk_by_animal_and_history(run):
    body = run("milk-by-animal", period=SEPTEMBER)
    rows = {r["animal_id"]: r for r in section(body, "animals")["rows"]}
    assert len(rows) == 20 and "D001" not in rows
    assert rows["M001"]["total"] == 17 * (11 + 8 + 8) and rows["M001"]["avg_per_day"] == 27.0
    assert rows["M016"]["afternoon"] == 0.0 and rows["M016"]["days_recorded"] == 17
    assert section(body, "animals")["totals"]["total"] == 8347.0
    history = run("milk-animal-history", period=SEPTEMBER, filters={"animal_id": "D001"})
    void_row = section(history, "history")["rows"][0]
    assert (void_row["status"], void_row["counts"]) == ("VOID", "No") and metric(history, "total") == 0
    assert run("milk-animal-history", filters={"animal_id": "NOPE"}, expect=422)


def test_milk_utilisation_does_not_assume_all_milk_is_sold(run):
    body = run("milk-utilisation", period=SEPTEMBER)
    totals = section(body, "utilisation")["totals"]
    assert totals["produced"] == 8347.0 and totals["sold"] == 4800.0
    assert (totals["calf_feed"], totals["domestic"], totals["wastage"]) == (720.0, 240.0, 60.0)  # VOID 77 L ignored
    assert totals["unaccounted"] == 12 * 6.0 + 5 * 491.0
    assert totals["sold"] < totals["produced"]


def test_monthly_milk_summary(run):
    body = run("milk-monthly-summary", period=CUSTOM)
    rows = section(body, "months")["rows"]
    assert [(r["month"], r["production_days"], r["total"]) for r in rows] == [
        ("August 2026", 1, 491.0), ("September 2026", 17, 8347.0)]


# ------------------------------------------------------------ feed and cost
def test_daily_feed_cost_and_cost_per_litre(run):
    body = run("feed-daily-cost", period=SEPTEMBER)
    assert D(str(metric(body, "cost"))) == EXPECTED["sep_feed_cost"]
    assert metric(body, "per_litre") == round(450000 / 8347, 4)
    assert all(c["status"] == "PASS" for c in body["reconciliation"])
    assert any("operational date" in note for note in body["notes"])


def test_feed_purchases_equal_finance_feed_expenses(run):
    body = run("feed-purchases", period=SEPTEMBER)
    assert D(str(metric(body, "amount"))) == D("500000.00")


def test_cost_reports_consume_the_cop_authority(farm, run):
    monthly = run("cost-monthly-summary", period=CUSTOM)
    rows = {r["period"]: r for r in section(monthly, "months")["rows"]}
    assert rows["August 2026"]["official_coml"] == 64.75 and rows["September 2026"]["official_coml"] is None
    authority = farm.get("/farm/coml/integrated", params={"period_start": "2026-09-01", "period_end": "2026-09-17"}).json()
    assert rows["September 2026"]["cop_per_litre"] == authority["costs"]["total_coml_per_liter"]
    official = run("cost-official-history")
    assert section(official, "official")["rows"][0]["coml_per_litre"] == 64.75


def test_zero_milk_denominator_is_reported_as_unavailable(run):
    body = run("cost-period", period={"mode": "CUSTOM", "start_date": "2026-07-01", "end_date": "2026-07-31"})
    assert metric(body, "cop") is None and any("No milk is recorded" in n for n in body["notes"])
    daily = run("cost-daily", period={"mode": "CUSTOM", "start_date": "2026-09-16", "end_date": "2026-09-18"})
    assert [r["date"] for r in section(daily, "days")["rows"]] == ["2026-09-16", "2026-09-17", "2026-09-18"]
    assert section(daily, "days")["rows"][2]["cop_per_litre"] is None
    assert run("cost-daily", period={"mode": "CALENDAR_YEAR", "year": 2026}, expect=422)


# ------------------------------------------------------------------ breeding
def test_breeding_status_uses_the_reproductive_authority(run):
    body = run("breed-status")
    rows = {r["animal_id"]: r for r in section(body, "status")["rows"]}
    assert len(rows) == 33                                        # 20 milking + 5 dry + 8 heifers
    assert rows["M001"]["reproductive_status"] == "Pregnant"
    assert rows["M001"]["expected_calving_date"] == "2027-05-11"   # 01-Aug-2026 + 283 days
    assert rows["M002"]["reproductive_status"] == "Bred" and rows["M002"]["pd_due_date"] == "2026-09-24"  # + 35 days
    assert rows["M005"]["reproductive_status"] == "Open"
    assert rows["M004"]["service_attempts"] == 3
    assert rows["H001"]["reproductive_status"] == "No breeding history"
    assert (rows["M001"]["lactation_number"], rows["M001"]["days_in_milk"]) == (1, 109)


def test_pd_due_respects_the_35_day_rule(run):
    due = {r["animal_id"]: r for r in section(run("breed-pd-due"), "pd")["rows"]}
    assert set(due) == {"M003"} and due["M003"]["pd_position"] == "Overdue" and due["M003"]["pd_due_date"] == "2026-09-09"
    everything = {r["animal_id"] for r in section(run("breed-pd-due", filters={"only_due": False}), "pd")["rows"]}
    assert everything == {"M002", "M003", "M004", "H002", "H003", "H004"}


def test_due_for_ai_pregnancies_and_repeat_breeders(run):
    due = {r["animal_id"] for r in section(run("breed-due-for-ai"), "due")["rows"]}
    assert len(due) == 24 and "M005" in due and "H001" in due
    assert not due & {"M001", "M002", "M003", "M004", "M006", "D001", "H002", "H003", "H004"}
    pregnant = {r["animal_id"]: r for r in section(run("breed-pregnancies"), "pregnancies")["rows"]}
    assert set(pregnant) == {"M001", "D001"}
    assert (pregnant["D001"]["expected_calving_date"], pregnant["D001"]["days_to_calving"]) == ("2026-09-29", 11)
    soon = section(run("breed-pregnancies", filters={"calving_within": "14"}), "pregnancies")["rows"]
    assert [r["animal_id"] for r in soon] == ["D001"]
    repeat = section(run("breed-repeat-breeders"), "repeat")["rows"]
    assert [(r["animal_id"], r["services"]) for r in repeat] == [("M004", 3)]


def test_insemination_calving_loss_history(run):
    ai = run("breed-inseminations", period=SEPTEMBER)
    assert metric(ai, "ai") == 4 and D(str(metric(ai, "cost"))) == D("6000.00")
    assert metric(run("breed-inseminations", period=SEPTEMBER, filters={"technician": "bilal"}), "ai") == 1
    calvings = run("breed-calvings", period=SEPTEMBER)
    row = section(calvings, "calvings")["rows"][0]
    assert row["animal_id"] == "M006" and "FC001" in row["calves"]
    losses = run("breed-pregnancy-losses", period={"mode": "MONTH", "year": 2026, "month": 8})
    row = section(losses, "losses")["rows"][0]
    assert (row["animal_id"], row["insemination_date"], row["days_carried"]) == ("M005", "2026-05-10", 97)


def test_technician_and_semen_performance(run):
    year = {"mode": "CALENDAR_YEAR", "year": 2026}
    rows = {r["key"]: r for r in section(run("breed-technician-performance", period=year), "performance")["rows"]}
    assert (rows["Bilal"]["cycles"], rows["Bilal"]["negative_pd"], rows["Bilal"]["conception_rate_percent"]) == (4, 2, 0.0)
    assert (rows["Dr. Asif"]["conceptions"], rows["Dr. Asif"]["pregnancy_losses"]) == (2, 1)
    lots = {r["key"]: r for r in section(run("breed-semen-lot-performance", period=year), "performance")["rows"]}
    assert lots["SL-001"]["cycles"] == 3 and D(str(lots["SL-001"]["total_semen_cost"])) == D("6000.00")
    inventory = section(run("breed-semen-inventory"), "semen")["rows"][0]
    assert (inventory["purchased"], inventory["used"], inventory["on_hand"]) == (20, 3, 17)
    assert D(str(inventory["stock_value"])) == D("34000.00") and inventory["expiry_position"] == "Expires within 90 days"


def test_reproductive_history_by_animal(run):
    body = run("breed-animal-history", filters={"animal_id": "M004"})
    cycles = section(body, "cycles")["rows"]
    assert [c["service_attempt"] for c in cycles] == [1, 2, 3]
    assert [c["outcome"] for c in cycles][:2] == ["Not Pregnant", "Not Pregnant"]
    assert len(section(body, "events")["rows"]) == 6


# -------------------------------------------------------------------- health
def test_health_cases_treatments_and_withdrawal(run):
    active = run("health-active-cases")
    row = section(active, "cases")["rows"][0]
    assert (row["case_id"], row["animal_id"], row["days_open"], row["treatments"]) == ("HC-0001", "M007", 8, 1)
    assert metric(active, "followup") == 1
    period = run("health-cases-period", period={"mode": "MONTH", "year": 2026, "month": 8})
    assert [r["case_id"] for r in section(period, "cases")["rows"]] == ["HC-0002"]

    withdrawal = run("health-withdrawal-status")
    row = section(withdrawal, "withdrawal")["rows"][0]
    assert (row["animal_id"], row["withdrawal_until"], row["days_remaining"]) == ("M007", "2026-09-20", 2)
    history = run("health-withdrawal-history", period=CUSTOM)
    assert {r["animal_id"]: r["withdrawal_position"] for r in section(history, "withdrawals")["rows"]} == {
        "M008": "Completed", "M007": "Active"}


def test_vaccination_is_reported_separately_from_health(run):
    due = run("health-vaccination-due")
    rows = {r["animal_id"]: r for r in section(due, "due")["rows"]}
    assert set(rows) == {"M001", "M002"}                          # VOID schedule for M004 is not due
    assert (rows["M001"]["position"], rows["M001"]["days"]) == ("Overdue", 8)
    assert (rows["M002"]["position"], rows["M002"]["days"]) == ("Upcoming", 7)
    assert set(r["animal_id"] for r in section(run("health-vaccination-due", filters={"within_days": "7"}), "due")["rows"]) == {"M001", "M002"}
    history = run("health-vaccination-history", period=SEPTEMBER)
    assert [r["animal_id"] for r in section(history, "history")["rows"]] == ["M003"]


def test_health_history_agrees_with_the_animal_passport(farm, run):
    body = run("health-animal-history", filters={"animal_id": "M007"})
    assert metric(body, "withdrawal") == "Yes" and len(section(body, "treatments")["rows"]) == 1
    passport = farm.get("/farm/animals/M007/treatments")
    if passport.status_code == 200:
        records = passport.json().get("records", [])
        assert len(records) == len(section(body, "treatments")["rows"])


# ---------------------------------------------------------------- management
def test_daily_farm_summary_equals_its_source_reports(run):
    body = run("mgmt-daily-summary", period={"as_of_date": "2026-09-05"})
    lines = {(r["area"], r["line"]): r["value"] for r in section(body, "figures")["rows"]}
    assert lines[("Herd", "Total herd")] == 48 and lines[("Milk", "Milk produced")] == 491.0
    assert lines[("Milk", "Milk sold")] == 400.0 and lines[("Milk", "Unaccounted milk")] == 6.0
    assert lines[("Finance", "Revenue recorded")] == 130000.0
    assert lines[("Feed", "Herd feed cost")] == 25000.0
    assert lines[("Finance", "Receivables outstanding")] == 200000.0


def test_period_summary_and_attention_report(run):
    summary = run("mgmt-period-summary", period=SEPTEMBER)
    lines = {(r["area"], r["line"]): r["value"] for r in section(summary, "figures")["rows"]}
    assert lines[("Finance", "Revenue")] == 1400000.0 and lines[("Finance", "Expenses")] == 750000.0
    assert lines[("Milk", "Milk produced")] == 8347.0 and lines[("Herd", "Deaths")] == 1
    assert lines[("Cost of Milk", "Cost of production per litre")] == round(566000 / 8347, 4)
    attention = {r["item"]: r["count"] for r in section(run("mgmt-attention"), "attention")["rows"]}
    assert attention["Animals under milk withdrawal"] == 1
    assert attention["Pregnancy diagnosis due or overdue"] == 1
    assert attention["Vaccinations overdue"] == 1
    assert attention["Calving expected within 14 days"] == 1
    assert attention["Receivables overdue (PKR)"] == 100000.0
    assert "Yield drop of 15% or more" not in attention          # steady yields: nothing to report
