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

FINANCE_UI = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "FinanceTab.tsx"
)


class FinanceTaxonomyUiShapeContractTest(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.finance = FINANCE.read_text(
            encoding="utf-8",
        )

        cls.ui = FINANCE_UI.read_text(
            encoding="utf-8",
        )

    def test_tmr_is_master_named_feed_authority(self):
        self.assertIn(
            "governed_tmr_catalog_names",
            self.finance,
        )

    def test_feed_taxonomy_remains_grouped_for_ui(self):
        self.assertIn(
            'taxonomies["FEED"] = {',
            self.finance,
        )

        self.assertIn(
            '"TMR_INGREDIENTS"',
            self.finance,
        )

    def test_flat_feed_items_share_same_tmr_list(self):
        self.assertIn(
            '"FEED": feed_items',
            self.finance,
        )

    def test_other_is_only_explicit_exception(self):
        self.assertIn(
            'if "Other" in feed_items:',
            self.finance,
        )

        self.assertIn(
            'feed_items.append("Other")',
            self.finance,
        )

    def test_equipment_purchase_is_retained(self):
        self.assertIn(
            'opex_groups["EQUIPMENT"]',
            self.finance,
        )

        self.assertIn(
            "EQUIPMENT_PURCHASE_ITEM",
            self.finance,
        )

    def test_opex_flat_items_are_retained(self):
        self.assertIn(
            '*all_items("OPEX")',
            self.finance,
        )

    def test_finance_ui_consumes_grouped_taxonomy(self):
        self.assertIn(
            "Object.entries("
            "taxonomy?.taxonomies?.[masterCategory]",
            "".join(self.ui.split()),
        )

    def test_finance_ui_does_not_rename_option_values(self):
        normalized = "".join(
            self.ui.split()
        )

        self.assertIn(
            "<optionkey={item}value={item}>{item}</option>",
            normalized,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
