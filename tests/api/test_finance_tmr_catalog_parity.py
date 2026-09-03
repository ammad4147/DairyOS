from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]

FINANCE = (
    ROOT
    / "src"
    / "dairyos"
    / "api"
    / "finance_ledger.py"
)

TMR = (
    ROOT
    / "src"
    / "dairyos"
    / "api"
    / "tmr.py"
)


class FinanceTmrCatalogParityContractTest(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.finance = FINANCE.read_text(
            encoding="utf-8",
        )

        cls.tmr = TMR.read_text(
            encoding="utf-8",
        )

    def test_tmr_owns_catalog_identity(self):
        self.assertIn(
            "def governed_tmr_catalog_names(factory)",
            self.tmr,
        )

        self.assertIn(
            "_ingredient_definitions(factory)",
            self.tmr,
        )

    def test_finance_taxonomy_uses_tmr_catalog(self):
        start = self.finance.index(
            "def finance_taxonomy()"
        )

        block = self.finance[start:]

        self.assertIn(
            "governed_tmr_catalog_names",
            block,
        )

    def test_legacy_finance_feed_list_is_not_unioned(self):
        start = self.finance.index(
            "def finance_taxonomy()"
        )

        block = self.finance[start:]

        self.assertNotIn(
            'all_items("FEED")',
            block,
        )

    def test_finance_feed_validation_is_tmr_governed(self):
        self.assertIn(
            'if entry.master_category == "FEED":',
            self.finance,
        )

        self.assertIn(
            "_is_governed_tmr_feed_item(",
            self.finance,
        )

    def test_other_remains_explicit_exception(self):
        self.assertIn(
            'entry.sub_category == "Other"',
            self.finance,
        )

        self.assertIn(
            'if "Other" in feed_items:',
            self.finance,
        )

        self.assertIn(
            'feed_items.append("Other")',
            self.finance,
        )

    def test_opex_still_uses_existing_governed_validation(self):
        self.assertIn(
            'entry.master_category == "OPEX"',
            self.finance,
        )

        self.assertIn(
            "valid_item(",
            self.finance,
        )

        self.assertIn(
            "EQUIPMENT_PURCHASE_ITEM",
            self.finance,
        )

    def test_both_taxonomy_surfaces_share_feed_list(self):
        self.assertIn(
            'taxonomies["FEED"] = {',
            self.finance,
        )

        self.assertIn(
            '"TMR_INGREDIENTS": list(feed_items)',
            " ".join(self.finance.split()),
        )

        self.assertIn(
            '"FEED": feed_items',
            self.finance,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
