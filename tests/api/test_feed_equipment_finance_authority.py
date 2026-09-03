from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]

FINANCE = (
    ROOT
    / "src/dairyos/api/finance_ledger.py"
)

EQUIPMENT = (
    ROOT
    / "src/dairyos/api/feed_equipment.py"
)

APP = ROOT / "src/dairyos/app.py"


class FeedEquipmentFinanceAuthorityContractTest(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.finance = FINANCE.read_text(
            encoding="utf-8",
        )
        cls.equipment = EQUIPMENT.read_text(
            encoding="utf-8",
        )
        cls.app = APP.read_text(
            encoding="utf-8",
        )

    def test_finance_has_explicit_equipment_purchase_item(self):
        self.assertIn(
            'EQUIPMENT_PURCHASE_ITEM = "Equipment Purchase"',
            self.finance,
        )

    def test_equipment_purchase_requires_name_specification(self):
        self.assertIn(
            "custom_name_required",
            self.finance,
        )
        self.assertIn(
            "Equipment Purchase",
            self.finance,
        )

    def test_equipment_purchase_is_exposed_in_opex_taxonomy(self):
        self.assertIn(
            "*all_items(\"OPEX\")",
            self.finance,
        )
        self.assertIn(
            "EQUIPMENT_PURCHASE_ITEM",
            self.finance,
        )

    def test_feed_equipment_comes_only_from_finance_purchase_rows(self):
        self.assertIn(
            "FINANCE_EQUIPMENT_PURCHASES",
            self.equipment,
        )
        self.assertIn(
            "_is_equipment_purchase",
            self.equipment,
        )

    def test_existing_generic_equipment_master_is_not_authority(self):
        self.assertNotIn(
            "factory.equipment",
            self.equipment,
        )
        self.assertNotIn(
            "/farm/equipment",
            self.equipment,
        )

    def test_equipment_status_has_no_automatic_default(self):
        self.assertIn(
            '"NOT_SET"',
            self.equipment,
        )
        self.assertIn(
            "MANUAL_ONLY",
            self.equipment,
        )

    def test_only_two_manual_status_values_are_allowed(self):
        self.assertIn(
            '"OPERATIONAL"',
            self.equipment,
        )
        self.assertIn(
            '"NON_OPERATIONAL"',
            self.equipment,
        )

    def test_status_is_append_only_audited(self):
        self.assertIn(
            "FeedRation(",
            self.equipment,
        )
        self.assertIn(
            "FEED_EQUIPMENT_STATUS:",
            self.equipment,
        )

    def test_equipment_purchase_is_excluded_from_operating_cop(self):
        coml = (
            ROOT
            / "src/dairyos/api/coml.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Equipment Purchase",
            coml,
        )
        self.assertIn(
            "continue",
            coml,
        )

    def test_feed_equipment_router_is_registered(self):
        self.assertIn(
            "feed_equipment_router",
            self.app,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
