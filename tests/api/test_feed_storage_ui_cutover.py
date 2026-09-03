from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]

FEED_UI = (
    ROOT
    / "src/DairyOS.Web/src/components/FeedTab.tsx"
)


class FeedStorageUiCutoverContractTest(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.source = FEED_UI.read_text(
            encoding="utf-8",
        )

    def test_tmr_is_above_feed_storage(self):
        tmr = self.source.index(
            "1. TMR IS THE PRIMARY FEED OPERATION"
        )
        storage = self.source.index(
            "2. FEED STORAGE STATUS"
        )
        equipment = self.source.index(
            "3. SIMPLE FINANCE-LINKED EQUIPMENT LIST"
        )

        self.assertLess(
            tmr,
            storage,
        )
        self.assertLess(
            storage,
            equipment,
        )

    def test_old_feed_and_nutrition_heading_is_removed(self):
        self.assertNotIn(
            "Feed & Nutrition",
            self.source,
        )

    def test_record_feed_usage_is_removed(self):
        self.assertNotIn(
            "Record Feed Usage",
            self.source,
        )
        self.assertNotIn(
            "recordUsage",
            self.source,
        )
        self.assertNotIn(
            "CONSUMPTION",
            self.source,
        )
        self.assertNotIn(
            "WASTAGE",
            self.source,
        )

    def test_storage_reads_authoritative_projection(self):
        self.assertIn(
            "/farm/feed-inventory/authoritative",
            self.source,
        )

    def test_storage_displays_tmr_consumption(self):
        self.assertIn(
            "TMR Consumed",
            self.source,
        )
        self.assertIn(
            "auto_consumed_from_tmr",
            self.source,
        )

    def test_manual_override_is_stock_correction_only(self):
        self.assertIn(
            "/farm/feed-inventory/manual-override",
            self.source,
        )
        self.assertIn(
            "This does not record feeding",
            self.source,
        )

    def test_old_generic_equipment_api_is_removed(self):
        self.assertNotIn(
            "/farm/equipment",
            self.source,
        )

    def test_feed_equipment_comes_from_finance_projection(self):
        self.assertIn(
            "/farm/feed-equipment",
            self.source,
        )
        self.assertIn(
            "Equipment purchased in Finance appears",
            self.source,
        )

    def test_equipment_status_is_manual_only(self):
        self.assertIn(
            "Operational",
            self.source,
        )
        self.assertIn(
            "Non-Operational",
            self.source,
        )
        normalized = " ".join(
            self.source.split()
        )

        self.assertIn(
            "does not infer equipment status",
            normalized,
        )

    def test_service_condition_hours_ui_is_removed(self):
        self.assertNotIn(
            "Next Service",
            self.source,
        )
        self.assertNotIn(
            "running_hours",
            self.source,
        )
        self.assertNotIn(
            "condition",
            self.source,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
