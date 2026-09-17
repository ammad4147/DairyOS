"""Source contracts of the Reporting screen (Settings -> Reporting)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "src" / "DairyOS.Web" / "src"
TAB = (WEB / "components" / "ReportingTab.tsx").read_text(encoding="utf-8")
CSS = (WEB / "components" / "Reporting.css").read_text(encoding="utf-8")


def test_screen_consumes_the_reports_api_only():
    for path in ("/farm/reports/catalog", "/farm/reports/run", "/farm/reports/export"):
        assert path in TAB
    assert "/farm/reporting/" not in TAB


def test_screen_holds_no_report_catalogue_field_list_or_calculation():
    # Areas, reports, filters, columns and totals all come from the backend.
    for leaked in ("photo_data", "lifecycle_status", "created_at", "non_milking", "Photo Data", "animal_type"):
        assert leaked not in TAB
    assert "reduce((sum" not in TAB and ".reduce((total" not in TAB


def test_today_never_comes_from_utc():
    assert "toISOString" not in TAB
    assert "operational_today" in TAB


def test_workflow_controls_exist():
    for control in ("Generate", "Print", "PDF", "Excel", "CSV", "Customize Columns", "Restore default columns",
                    "From Date", "To Date", "As of Date", "Quarter", "Reconciliation Controls"):
        assert control in TAB, control
    assert "aria-sort" in TAB and "_drill" in TAB and "page_size" in TAB


def test_print_is_a_print_ready_pdf_not_the_native_webview_dialog():
    assert "window.print()" not in TAB
    assert "await exportReport('PDF')" in TAB
    assert "save_reporting_export" in TAB          # desktop save dialog contract


def test_values_never_render_null_or_undefined():
    assert "if (value === null || value === undefined || value === '') return '';" in TAB


def test_styles_are_real_css_not_missing_utility_classes():
    assert 'className="space-y-4"' not in TAB and "bg-slate" not in TAB
    for rule in (".rpt-table th{position:sticky", ".rpt-table tfoot td", "@media print", ".rpt-card"):
        assert rule in CSS, rule
