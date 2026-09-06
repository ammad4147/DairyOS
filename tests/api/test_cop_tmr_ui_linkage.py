from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]

COP = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "COML.tsx"
)

APP = ROOT / "src" / "DairyOS.Web" / "src" / "App.tsx"

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
        cls.cop_source = COP.read_text(encoding="utf-8")
        cls.app_source = APP.read_text(encoding="utf-8")
        cls.dashboard_source = DASHBOARD.read_text(encoding="utf-8")

    def test_single_combined_cop_surface_is_used(self):
        self.assertIn("Cost of Production (COP)", self.cop_source)
        self.assertIn("Estimated COP", self.cop_source)
        self.assertIn("Operator-Assessed COP", self.cop_source)
        self.assertIn("currentView==='cop'&&<COML/>", self.app_source)
        self.assertNotIn("COPOfficializationPanel", self.app_source)

    def test_integrated_cop_endpoint_is_used(self):
        self.assertIn("/farm/coml/integrated", self.cop_source)

    def test_auto_period_controls_are_present(self):
        for text in (
            "Analysis Period",
            "This month",
            "Last 30 days",
            "Year to date",
            "From",
            "To",
        ):
            self.assertIn(text, self.cop_source)
        self.assertIn("live month-to-date", self.cop_source)
        self.assertIn("calendarEnd", self.cop_source)

    def test_selected_month_official_record_is_loaded(self):
        self.assertIn("month_start: officialMonthStart", self.cop_source)
        self.assertIn("`${API_BASE}/farm/coml?${officialQuery}`", self.cop_source)

    def test_current_only_official_endpoint_is_not_used_by_cop_surface(self):
        self.assertNotIn("/farm/coml/current", self.cop_source)

    def test_primary_auto_surface_has_four_metrics(self):
        for label in (
            "Milk in period (L)",
            "Feed Cost / L",
            "Estimated OPEX / L",
            "Estimated COP / L",
        ):
            self.assertIn(label, self.cop_source)

    def test_tmr_is_visible_feed_authority(self):
        self.assertIn("Governed TMR ration × active DairyOS herd", self.cop_source)
        self.assertIn("TMR_HERD_COST+FINANCE_OPEX", self.cop_source)
        self.assertIn("TMR Feed/L", self.cop_source)

    def test_finance_remains_opex_authority(self):
        self.assertIn("Finance expenses classified OPEX", self.cop_source)
        self.assertIn("Finance OPEX", self.cop_source)

    def test_bulk_feed_purchase_is_not_consumption(self):
        self.assertIn(
            "not treated as same-day consumption in COP",
            self.cop_source,
        )

    def test_auto_cop_can_be_declared_official_on_primary_surface(self):
        self.assertIn("Make Estimated COP / L Official", self.cop_source)
        self.assertIn("/farm/coml/lock", self.cop_source)
        self.assertIn(
            "Making Estimated COP official replaces the month’s current official COP/L.",
            self.cop_source,
        )

    def test_auto_refresh_is_present(self):
        self.assertIn("60_000", self.cop_source)
        self.assertIn("auto-refresh every 60 seconds", self.cop_source)

    def test_manual_calculator_is_direct_per_litre_entry(self):
        self.assertIn("Operator-Assessed COP", self.cop_source)
        self.assertIn("Manual Feed Cost per Liter", self.cop_source)
        self.assertIn("Manual OPEX per Liter", self.cop_source)
        self.assertIn("Feed Cost/L + OPEX/L", self.cop_source)
        self.assertNotIn("/farm/coml/calculate", self.cop_source)

    def test_manual_cop_can_replace_the_monthly_official_value(self):
        self.assertIn("Make Operator-Assessed COP / L Official", self.cop_source)
        self.assertIn(
            "Making Operator-Assessed COP/L official replaces the month’s current official COP/L",
            self.cop_source,
        )

    def test_manual_draft_is_persisted_but_milk_remains_automatic(self):
        self.assertIn("dairyos_cop_manual_per_litre_draft", self.cop_source)
        self.assertIn("dairyos_cop_manual_per_litre_draft", self.cop_source)

    def test_dashboard_uses_persisted_official_cop_not_live_auto(self):
        self.assertIn("/farm/coml/current", self.dashboard_source)
        self.assertIn("record?.total_coml_per_liter", self.dashboard_source)
        self.assertNotIn("/farm/coml/integrated", self.dashboard_source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
