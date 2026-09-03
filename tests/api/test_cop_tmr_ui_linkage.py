from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]

COP = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "COPOfficializationPanel.tsx"
)


class CopTmrUiLinkageContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = COP.read_text(
            encoding="utf-8",
        )

    def test_integrated_cop_endpoint_is_used(self):
        self.assertIn(
            "/farm/coml/integrated",
            self.source,
        )

    def test_current_month_is_month_to_date(self):
        self.assertIn(
            "live month-to-date",
            self.source,
        )
        self.assertIn(
            "month === today.slice(0, 7)",
            self.source,
        )

    def test_historical_month_uses_calendar_end(self):
        self.assertIn(
            "calendarEnd",
            self.source,
        )
        self.assertIn(
            "completed calendar period",
            self.source,
        )

    def test_selected_month_official_record_is_loaded(self):
        self.assertIn(
            "month_start: range.start",
            self.source,
        )
        self.assertIn(
            "`${API_BASE}/farm/coml?${officialQuery}`",
            self.source,
        )

    def test_current_only_official_endpoint_is_not_used(self):
        self.assertNotIn(
            "/farm/coml/current",
            self.source,
        )

    def test_tmr_is_visible_feed_authority(self):
        self.assertIn(
            "TMR Feed / L",
            self.source,
        )
        self.assertIn(
            "Governed TMR ration ×",
            self.source,
        )

    def test_finance_remains_opex_authority(self):
        self.assertIn(
            "Finance OPEX / L",
            self.source,
        )

    def test_bulk_feed_purchase_is_not_consumption(self):
        self.assertIn(
            "not treated as same-day",
            self.source,
        )
        self.assertIn(
            "consumption in COP",
            self.source,
        )

    def test_auto_cop_officialization_remains(self):
        self.assertIn(
            "Make Auto COP / L Official",
            self.source,
        )
        self.assertIn(
            "/farm/coml/lock",
            self.source,
        )

    def test_existing_official_record_prevents_duplicate_button_action(self):
        self.assertIn(
            "selectedMonthIsOfficial",
            self.source,
        )
        self.assertIn(
            "Official COP Recorded",
            self.source,
        )

    def test_auto_refresh_is_present(self):
        self.assertIn(
            "60_000",
            self.source,
        )
        self.assertIn(
            "auto-refresh every 60 seconds",
            self.source,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
