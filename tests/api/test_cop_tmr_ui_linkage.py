from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]

AUTO_COP = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "COPOfficializationPanel.tsx"
)

MANUAL_COP = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "COML.tsx"
)

APP = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "App.tsx"
)

DASHBOARD = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "UnifiedDashboard.tsx"
)


class CopTmrUiLinkageContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.auto_source = AUTO_COP.read_text(encoding="utf-8")
        cls.manual_source = MANUAL_COP.read_text(encoding="utf-8")
        cls.app_source = APP.read_text(encoding="utf-8")
        cls.dashboard_source = DASHBOARD.read_text(encoding="utf-8")

    def test_integrated_cop_endpoint_is_used(self):
        self.assertIn(
            "/farm/coml/integrated",
            self.auto_source,
        )

    def test_current_month_is_month_to_date(self):
        self.assertIn(
            "live month-to-date",
            self.auto_source,
        )
        self.assertIn(
            "month === today.slice(0, 7)",
            self.auto_source,
        )

    def test_historical_month_uses_calendar_end(self):
        self.assertIn(
            "calendarEnd",
            self.auto_source,
        )
        self.assertIn(
            "completed calendar period",
            self.auto_source,
        )

    def test_selected_month_official_record_is_loaded(self):
        self.assertIn(
            "month_start: range.start",
            self.auto_source,
        )
        self.assertIn(
            "`${API_BASE}/farm/coml?${officialQuery}`",
            self.auto_source,
        )

    def test_current_only_official_endpoint_is_not_used_by_auto_panel(self):
        self.assertNotIn(
            "/farm/coml/current",
            self.auto_source,
        )

    def test_tmr_is_visible_feed_authority(self):
        self.assertIn(
            "TMR Feed / L",
            self.auto_source,
        )
        self.assertIn(
            "Governed TMR ration ×",
            self.auto_source,
        )
        self.assertIn(
            "active DairyOS herd",
            self.auto_source,
        )

    def test_finance_remains_opex_authority(self):
        self.assertIn(
            "Finance OPEX / L",
            self.auto_source,
        )

    def test_bulk_feed_purchase_is_not_consumption(self):
        self.assertIn(
            "not treated as same-day consumption in COP",
            self.auto_source,
        )

    def test_auto_cop_can_always_be_declared_official_when_calculable(self):
        self.assertIn(
            "Make Auto COP / L Official",
            self.auto_source,
        )
        self.assertIn(
            "/farm/coml/lock",
            self.auto_source,
        )
        self.assertNotIn(
            "selectedMonthIsOfficial",
            self.auto_source,
        )
        self.assertIn(
            "Making Auto official replaces the month’s current official COP/L.",
            self.auto_source,
        )

    def test_auto_refresh_is_present(self):
        self.assertIn(
            "60_000",
            self.auto_source,
        )
        self.assertIn(
            "auto-refresh every 60 seconds",
            self.auto_source,
        )

    def test_manual_calculator_is_direct_per_litre_entry(self):
        self.assertIn(
            "Manual COP / L Calculator",
            self.manual_source,
        )
        self.assertIn(
            "Manual Feed Cost per Liter",
            self.manual_source,
        )
        self.assertIn(
            "Manual OPEX per Liter",
            self.manual_source,
        )
        self.assertIn(
            "Feed Cost/L + OPEX/L",
            self.manual_source,
        )
        self.assertNotIn(
            "/farm/coml/calculate",
            self.manual_source,
        )

    def test_manual_cop_can_replace_the_monthly_official_value(self):
        self.assertIn(
            "Make Manual COP / L Official",
            self.manual_source,
        )
        self.assertIn(
            "/farm/coml/lock",
            self.manual_source,
        )
        self.assertIn(
            "replaces the month’s current official COP/L",
            self.manual_source,
        )

    def test_both_manual_and_auto_surfaces_are_rendered_on_cop_tab(self):
        self.assertIn(
            "currentView==='cop'&&<><COML/><COPOfficializationPanel/></>",
            self.app_source,
        )

    def test_dashboard_uses_persisted_official_cop_not_live_auto(self):
        self.assertIn(
            "/farm/coml/current",
            self.dashboard_source,
        )
        self.assertIn(
            "record?.total_coml_per_liter",
            self.dashboard_source,
        )
        self.assertNotIn(
            "/farm/coml/integrated",
            self.dashboard_source,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)