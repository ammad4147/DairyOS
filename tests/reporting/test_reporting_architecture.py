"""Contracts of the Reporting architecture: catalogue, periods, engine,
field exposure, exports and permissions."""

from __future__ import annotations

import csv
import io
from datetime import date

import pytest
from openpyxl import load_workbook

from dairyos.api.authorization import permission_for_request
from dairyos.reporting.periods import PeriodError, month_sequence, quarter_sequence, resolve_period
from dairyos.reporting.registry import AREAS, REPORT_BY_ID, REPORTS
from tests.reporting.conftest import section

TODAY = date(2026, 9, 18)
SEPTEMBER = {"mode": "MONTH", "year": 2026, "month": 9}

FORBIDDEN_COLUMN_KEYS = {
    "id", "photo_data", "created_at", "updated_at", "active", "lifecycle_status", "is_currently_milking",
    "non_milking_directive", "non_milking_changed_by", "non_milking_restore_to_milking", "animal_type",
    "session_ledger", "source_event_id", "password_hash", "permissions_json", "cop_classification",
}


# -------------------------------------------------------------- catalogue
def test_catalogue_is_organised_by_management_area():
    assert [a.title for a in AREAS] == ["Herd", "Milk", "Feed", "Breeding", "Health", "Finance", "Cost of Milk", "Management"]
    for area in AREAS:
        assert [d for d in REPORTS if d.area == area.id], f"{area.title} has no report"
    titles = [d.title for d in REPORTS]
    assert len(titles) == len(set(titles)), "duplicate report titles"
    assert len(REPORTS) >= 60


def test_every_report_declares_purpose_authority_and_operator_columns():
    for definition in REPORTS:
        assert len(definition.purpose) > 25 and definition.authority, definition.id
        assert definition.basis in {"RECORDED", "CALCULATED", "DERIVED"}
        keys = {c.key for c in definition.columns}
        assert not keys & FORBIDDEN_COLUMN_KEYS, (definition.id, keys & FORBIDDEN_COLUMN_KEYS)
        for column in definition.columns:
            assert "_" not in column.label and column.label == column.label.strip(), (definition.id, column.label)
            assert column.tier in {"default", "optional", "advanced"}
        if definition.columns:
            assert any(c.tier == "default" for c in definition.columns), definition.id
        if definition.default_sort and definition.columns:
            assert definition.default_sort[0] in keys, definition.id


def test_category_terminology_is_canonical():
    titles = {d.title for d in REPORTS if d.area == "herd"}
    assert {"Milking Cows", "Dry Cows", "Heifers", "Female Calves", "Male Calves", "Bulls"} <= titles
    options = dict(next(f for f in REPORT_BY_ID["herd-register"].filters if f.key == "category").options)
    assert options == {"Milking": "Milking Cows", "Dry": "Dry Cows", "Heifer": "Heifers",
                       "Female Calf": "Female Calves", "Male Calf": "Male Calves", "Bull": "Bulls"}


def test_filters_are_report_specific():
    assert {f.key for f in REPORT_BY_ID["herd-milking"].filters} == {"breed", "location", "production_group"}
    assert {f.key for f in REPORT_BY_ID["herd-bull"].filters} == {"breed", "location"}
    assert REPORT_BY_ID["fin-revenue-expense-reconciliation"].filters == ()
    assert REPORT_BY_ID["fin-revenue-expense-reconciliation"].period == "range"
    assert REPORT_BY_ID["herd-register"].period == "none"          # category history does not exist


def test_catalog_endpoint(farm):
    body = farm.get("/farm/reports/catalog").json()
    assert body["operational_today"] == "2026-09-18" and body["currency"] == "PKR"
    assert [a["title"] for a in body["areas"]][:2] == ["Herd", "Milk"]
    assert {"MONTH", "QUARTER", "CUSTOM", "YEAR_TO_DATE"} <= {m["value"] for m in body["period_modes"]}
    assert "Holstein Friesian" in {o["value"] for o in body["option_sources"]["breeds"]}
    assert "SECRETPHOTOBYTES" not in farm.get("/farm/reports/catalog").text


# ---------------------------------------------------------------- periods
@pytest.mark.parametrize("spec, start, end", [
    ({"mode": "TODAY"}, date(2026, 9, 18), date(2026, 9, 18)),
    ({"mode": "YESTERDAY"}, date(2026, 9, 17), date(2026, 9, 17)),
    ({"mode": "CURRENT_MONTH"}, date(2026, 9, 1), date(2026, 9, 30)),
    ({"mode": "PREVIOUS_MONTH"}, date(2026, 8, 1), date(2026, 8, 31)),
    ({"mode": "CURRENT_QUARTER"}, date(2026, 7, 1), date(2026, 9, 30)),
    ({"mode": "PREVIOUS_QUARTER"}, date(2026, 4, 1), date(2026, 6, 30)),
    ({"mode": "YEAR_TO_DATE"}, date(2026, 1, 1), date(2026, 9, 18)),
    ({"mode": "CALENDAR_YEAR", "year": 2025}, date(2025, 1, 1), date(2025, 12, 31)),
    ({"mode": "MONTH", "year": 2024, "month": 2}, date(2024, 2, 1), date(2024, 2, 29)),
    ({"mode": "QUARTER", "year": 2026, "quarter": 1}, date(2026, 1, 1), date(2026, 3, 31)),
    ({"mode": "QUARTER", "year": 2026, "quarter": 2}, date(2026, 4, 1), date(2026, 6, 30)),
    ({"mode": "QUARTER", "year": 2026, "quarter": 4}, date(2026, 10, 1), date(2026, 12, 31)),
    ({"mode": "CUSTOM", "start_date": "2026-12-31", "end_date": "2027-01-01"}, date(2026, 12, 31), date(2027, 1, 1)),
])
def test_period_resolution(spec, start, end):
    period = resolve_period("range", spec, operational_today=TODAY)
    assert (period.start, period.end) == (start, end)
    assert period.contains(start) and period.contains(end)
    assert not period.contains(date.fromordinal(start.toordinal() - 1))
    assert not period.contains(date.fromordinal(end.toordinal() + 1))


def test_previous_quarter_crosses_the_year_boundary():
    period = resolve_period("range", {"mode": "PREVIOUS_QUARTER"}, operational_today=date(2027, 2, 10))
    assert (period.start, period.end) == (date(2026, 10, 1), date(2026, 12, 31))
    period = resolve_period("range", {"mode": "PREVIOUS_MONTH"}, operational_today=date(2027, 1, 5))
    assert (period.start, period.end) == (date(2026, 12, 1), date(2026, 12, 31))


@pytest.mark.parametrize("spec", [
    {"mode": "CUSTOM", "start_date": "2026-09-10", "end_date": "2026-09-01"},
    {"mode": "CUSTOM", "start_date": "2026-09-10"},
    {"mode": "CUSTOM", "start_date": "not-a-date", "end_date": "2026-09-01"},
    {"mode": "MONTH", "year": 2026, "month": 13},
    {"mode": "QUARTER", "year": 2026, "quarter": 5},
    {"mode": "DECADE"},
])
def test_invalid_periods_are_rejected(spec):
    with pytest.raises(PeriodError):
        resolve_period("range", spec, operational_today=TODAY)


def test_month_and_quarter_sequences_clip_to_the_range():
    assert month_sequence(date(2026, 8, 10), date(2026, 9, 17)) == [
        (date(2026, 8, 10), date(2026, 8, 31)), (date(2026, 9, 1), date(2026, 9, 17))]
    assert quarter_sequence(date(2026, 12, 15), date(2027, 1, 15)) == [
        (date(2026, 12, 15), date(2026, 12, 31)), (date(2027, 1, 1), date(2027, 1, 15))]


def test_today_follows_the_farm_clock_not_utc(farm, monkeypatch, run):
    """00:30 PKT on 19-Sep is still 18-Sep in UTC. Reporting must say 19-Sep."""
    import datetime as _dt
    from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService
    from tests.reporting.synthetic_farm import PKT

    monkeypatch.setattr(FarmSettingsService, "get_operational_datetime",
                        lambda self: _dt.datetime(2026, 9, 19, 0, 30, tzinfo=PKT))
    body = run("fin-daily-activity", period={"mode": "TODAY"})
    assert body["period"]["start_date"] == "2026-09-19" and body["period"]["operational_today"] == "2026-09-19"


def test_future_period_runs_and_is_empty(run):
    body = run("fin-revenue-expense-reconciliation", period={"mode": "MONTH", "year": 2031, "month": 1})
    assert body["summary"][0]["value"] == 0 and all(c["status"] == "PASS" for c in body["reconciliation"])
    assert run("cost-period", period={"mode": "MONTH", "year": 2031, "month": 1})["summary"][0]["value"] is None


# ----------------------------------------------------------------- engine
def test_unknown_report_filter_column_and_sort_are_rejected(farm, run):
    assert farm.post("/farm/reports/run", json={"report_id": "no-such-report"}).status_code == 404
    assert "does not support" in run("herd-bull", filters={"production_group": "X"}, expect=422)["detail"]
    assert "Unsupported column" in run("herd-register", columns=["animal_id", "photo_data"], expect=422)["detail"]
    assert "at least one" in run("herd-register", columns=[], expect=422)["detail"].lower()
    assert "unique" in run("herd-register", columns=["animal_id", "animal_id"], expect=422)["detail"]
    assert "sort" in run("herd-register", sort_key="photo_data", expect=422)["detail"].lower()
    assert "Unsupported value" in run("herd-register", filters={"category": "Camel"}, expect=422)["detail"]


def test_server_side_sorting_and_pagination(run):
    first = run("herd-register", sort_key="animal_id", sort_dir="desc", page=1, page_size=10)
    paging = section(first, "register")["paging"]
    assert (paging["total_rows"], paging["pages"], paging["page_size"]) == (48, 5, 10)
    assert len(section(first, "register")["rows"]) == 10
    assert section(first, "register")["rows"][0]["animal_id"] == "MC006"
    last = run("herd-register", sort_key="animal_id", sort_dir="desc", page=5, page_size=10)
    assert len(section(last, "register")["rows"]) == 8
    numeric = run("milk-by-animal", period=SEPTEMBER, sort_key="total", sort_dir="desc")
    totals = [r["total"] for r in section(numeric, "animals")["rows"]]
    assert totals == sorted(totals, reverse=True)
    # Totals always describe the whole result, never just the visible page.
    paged = run("milk-by-animal", period=SEPTEMBER, page_size=5)
    assert section(paged, "animals")["totals"]["total"] == 8347.0 and len(section(paged, "animals")["rows"]) == 5


def test_column_customisation_keeps_catalogue_order(run):
    body = run("herd-register", columns=["sire_id", "animal_id", "rfid"])
    assert [c["key"] for c in section(body, "register")["columns"]] == ["animal_id", "rfid", "sire_id"]
    assert set(section(body, "register")["rows"][0]) == {"animal_id", "rfid", "sire_id"}


# ------------------------------------------------------- security / exposure
def test_no_report_or_export_leaks_binary_or_internal_data(farm):
    for definition in REPORTS:
        filters = {"animal_id": "M001"} if any(f.required for f in definition.filters) else {}
        text = farm.post("/farm/reports/run", json={"report_id": definition.id, "filters": filters}).text
        for leak in ("SECRETPHOTOBYTES", "photo_data", "password", "undefined", "<dairyos.", "object at 0x"):
            assert leak not in text, (definition.id, leak)
    csv_text = farm.post("/farm/reports/export?format=CSV", json={
        "report_id": "herd-register", "columns": [c.key for c in REPORT_BY_ID["herd-register"].columns]}).text
    assert "SECRETPHOTOBYTES" not in csv_text and "None" not in csv_text and "null" not in csv_text


def test_each_report_requires_its_own_module_permission():
    assert permission_for_request("GET", "/farm/reports/catalog") == "settings.view"
    for report_id, permission in (("fin-transaction-ledger", "finance.view"), ("herd-register", "animals.view"),
                                  ("milk-by-animal", "milk.view"), ("breed-status", "breeding.view"),
                                  ("health-treatments", "health.view"), ("cost-period", "coml.view"),
                                  ("feed-inventory", "feed.view"), ("unknown", "settings.view")):
        assert permission_for_request("POST", "/farm/reports/run", {"report_id": report_id}) == permission
        assert permission_for_request("POST", "/farm/reports/export", {"report_id": report_id}) == permission


# ---------------------------------------------------------------- exports
def _export(farm, fmt, **body):
    response = farm.post(f"/farm/reports/export?format={fmt}", json=body)
    assert response.status_code == 200, response.text
    return response


def test_excel_export_matches_the_report_and_keeps_numbers_numeric(farm, run):
    request = {"report_id": "fin-revenue-expense-reconciliation", "period": SEPTEMBER}
    body = run(**{"report_id": request["report_id"], "period": SEPTEMBER})
    response = _export(farm, "XLSX", **request)
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert "2026-09-01_to_2026-09-30" in response.headers["content-disposition"]
    workbook = load_workbook(io.BytesIO(response.content))
    assert workbook.sheetnames == ["Report", "Revenue", "Expenses", "Management Position"]
    cover = {row[0]: row[1] for row in workbook["Report"].iter_rows(values_only=True) if row and row[0]}
    assert cover["Period"].startswith("September 2026") and cover["Total Revenue"] == 1400000

    sheet = workbook["Revenue"]
    header = [cell.value for cell in sheet[1]]
    gross = header.index("Gross Amount (PKR)") + 1
    values = [sheet.cell(row=r, column=gross).value for r in range(2, sheet.max_row + 1)]
    assert all(isinstance(v, (int, float)) for v in values)
    assert values[-1] == 1400000 == sum(values[:-1])                      # totals row equals its detail
    assert sheet.cell(row=2, column=gross).number_format == "#,##0.00"
    assert sheet.cell(row=sheet.max_row, column=1).value == "Total Revenue"
    exported = [sheet.cell(row=r, column=gross).value for r in range(2, sheet.max_row)]
    assert exported == [row["gross"] for row in section(body, "revenue")["rows"]]


def test_exports_honour_selected_columns_filters_and_full_row_set(farm):
    request = {"report_id": "herd-register", "columns": ["animal_id", "breed"], "filters": {"category": "Bull"},
               "page": 1, "page_size": 1}
    response = _export(farm, "CSV", **request)
    assert response.headers["X-DairyOS-Record-Count"] == "2" and response.headers["X-DairyOS-Column-Count"] == "2"
    lines = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
    header_index = lines.index(["Animal ID", "Breed"])
    assert [row[0] for row in lines[header_index + 1:]] == ["B001", "B002"]   # page_size ignored: every row exported
    assert ["Category", "Bulls"] in lines

    all_rows = _export(farm, "XLSX", report_id="fin-transaction-ledger", period={"mode": "CALENDAR_YEAR", "year": 2026},
                       page_size=5)
    ledger = load_workbook(io.BytesIO(all_rows.content))["Transactions"]
    assert ledger.max_row - 2 == int(all_rows.headers["X-DairyOS-Record-Count"]) > 5
    date_cell = ledger.cell(row=2, column=1)
    assert date_cell.is_date and date_cell.number_format == "DD-MMM-YYYY"


def test_csv_money_is_plain_numeric_and_pdf_is_a_pdf(farm):
    text = _export(farm, "CSV", report_id="fin-receivables").content.decode("utf-8-sig")
    assert "350000.00" in text and "PKR 350" not in text
    pdf = _export(farm, "PDF", report_id="fin-revenue-expense-reconciliation", period=SEPTEMBER).content
    assert pdf[:5] == b"%PDF-" and len(pdf) > 3000
    wide = _export(farm, "PDF", report_id="herd-register", columns=[c.key for c in REPORT_BY_ID["herd-register"].columns])
    assert wide.content[:5] == b"%PDF-"


def test_large_report_is_paged_not_dumped(farm, run):
    """A full calendar year of per-animal milk stays bounded on screen."""
    body = run("fin-transaction-ledger", period={"mode": "CALENDAR_YEAR", "year": 2026}, page_size=10)
    assert len(section(body, "ledger")["rows"]) == 10 and section(body, "ledger")["paging"]["total_rows"] > 30
    assert farm.post("/farm/reports/run", json={"report_id": "herd-register", "page_size": 100000}).status_code == 422
