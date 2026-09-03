from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
UI = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "TMRPreparationTool.tsx"
)


class TmrUiOverhaulContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = UI.read_text(encoding="utf-8")

    def test_old_browser_local_storage_authority_is_removed(self):
        self.assertNotIn(
            "localStorage",
            self.source,
        )
        self.assertNotIn(
            "STORAGE_KEY",
            self.source,
        )

    def test_api_fallback_is_not_markdown_corrupted(self):
        self.assertNotIn(
            "[http",
            self.source,
        )
        self.assertIn(
            "'http' + '://127.0.0.1:8000'",
            self.source,
        )

    def test_tmr_reads_governed_backend_summary(self):
        self.assertIn(
            "/farm/tmr",
            self.source,
        )

    def test_stage_versions_are_saved_through_backend(self):
        self.assertIn(
            "/farm/tmr/stages",
            self.source,
        )
        self.assertIn(
            "Save TMR",
            self.source,
        )

    def test_add_ingredient_uses_shared_catalog_endpoint(self):
        self.assertIn(
            "/farm/tmr/ingredients",
            self.source,
        )
        self.assertIn(
            "Add Ingredient",
            self.source,
        )
        self.assertIn(
            "Finance → Feed Expenses",
            self.source,
        )

    def test_weekly_vet_endorsement_is_present(self):
        self.assertIn(
            "/farm/tmr/endorse",
            self.source,
        )
        self.assertIn(
            "Weekly Vet TMR Review",
            self.source,
        )
        self.assertIn(
            "Vet Endorse TMR Review",
            self.source,
        )

    def test_all_six_dairyos_categories_are_visible(self):
        for category in (
            "Milking",
            "Dry",
            "Heifer",
            "Female Calf",
            "Male Calf",
            "Bull",
        ):
            self.assertIn(category, self.source)

    def test_milking_average_basis_is_explained(self):
        self.assertIn(
            "Average of Early, Mid and Late Lactation TMR",
            self.source,
        )

    def test_dry_average_basis_is_explained(self):
        self.assertIn(
            "Average of Far-Off Dry and Close-Up Dry TMR",
            self.source,
        )

    def test_cost_per_head_day_is_prominent(self):
        self.assertIn(
            "Cost / Head / Day",
            self.source,
        )
        self.assertIn(
            "category.cost_per_head_day",
            self.source,
        )

    def test_whole_herd_daily_cost_is_displayed(self):
        self.assertIn(
            "Whole Herd Feed Cost / Day",
            self.source,
        )
        self.assertIn(
            "total_herd_feed_cost_per_day",
            self.source,
        )

    def test_live_feed_cost_per_litre_is_displayed(self):
        self.assertIn(
            "Live Feed Cost / L",
            self.source,
        )
        self.assertIn(
            "feed_cost_per_litre_today",
            self.source,
        )

    def test_tmr_is_declared_as_cop_feed_authority(self):
        self.assertIn(
            "TMR whole-herd feed cost is the governed",
            self.source,
        )
        self.assertIn(
            "Feed Cost / L input to Auto COP",
            self.source,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
