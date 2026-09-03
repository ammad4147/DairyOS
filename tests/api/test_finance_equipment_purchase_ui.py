from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]

FINANCE_UI = (
    ROOT
    / "src/DairyOS.Web/src/components/FinanceTab.tsx"
)


class FinanceEquipmentPurchaseUiContractTest(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.source = FINANCE_UI.read_text(
            encoding="utf-8",
        )

    def test_equipment_purchase_sends_name_as_custom_specification(self):
        self.assertIn(
            "subCategory==='Equipment Purchase'",
            self.source,
        )
        self.assertIn(
            "?customSpecification:null",
            self.source,
        )

    def test_equipment_name_input_is_visible(self):
        self.assertIn(
            "'Equipment name'",
            self.source,
        )

    def test_other_custom_specification_still_remains(self):
        self.assertIn(
            "subCategory==='Other'",
            self.source,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
