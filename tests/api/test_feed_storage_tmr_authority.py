from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]

FEED = (
    ROOT
    / "src/dairyos/api/feed_inventory.py"
)

PROJECTION = (
    ROOT
    / "src/dairyos/api/feed_inventory_projection.py"
)


class FeedStorageTmrAuthorityContractTest(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.feed = FEED.read_text(
            encoding="utf-8",
        )
        cls.projection = PROJECTION.read_text(
            encoding="utf-8",
        )

    def test_direct_record_feed_usage_is_retired(self):
        self.assertIn(
            "Direct Record Feed Usage is retired",
            self.feed,
        )
        self.assertIn(
            '{"CONSUMPTION", "WASTAGE"}',
            self.feed,
        )

    def test_tmr_auto_consumption_has_daily_marker(self):
        self.assertIn(
            "TMR_AUTO_CONSUMPTION_DATE=",
            self.feed,
        )
        self.assertIn(
            "/automatic-consumption/sync",
            self.feed,
        )

    def test_tmr_consumption_uses_category_head_counts(self):
        self.assertIn(
            "animal_count",
            self.feed,
        )
        self.assertIn(
            "average_per_head",
            self.feed,
        )
        self.assertIn(
            "_tmr_ingredient_requirement",
            self.feed,
        )

    def test_today_can_reconcile_but_closed_days_are_locked(self):
        self.assertIn(
            "LOCKED_DAILY_AUTO_TMR",
            self.feed,
        )
        self.assertIn(
            "target_signed - existing_signed",
            self.feed,
        )

    def test_manual_override_is_separate_signed_adjustment(self):
        self.assertIn(
            "FEED_STORAGE_MANUAL_OVERRIDE",
            self.feed,
        )
        self.assertIn(
            "/manual-override",
            self.feed,
        )
        self.assertIn(
            "quantity_delta",
            self.feed,
        )

    def test_projection_exposes_tmr_consumption(self):
        self.assertIn(
            "auto_consumed_from_tmr",
            self.projection,
        )
        self.assertIn(
            "GOVERNED_TMR_X_ACTIVE_HERD",
            self.projection,
        )

    def test_projection_exposes_manual_override(self):
        self.assertIn(
            "manual_override_net",
            self.projection,
        )
        self.assertIn(
            "SIGNED_PHYSICAL_STOCK_ADJUSTMENT",
            self.projection,
        )

    def test_storage_shortage_is_explicit(self):
        self.assertIn(
            '"shortage"',
            self.projection,
        )
        self.assertIn(
            '"SHORTAGE"',
            self.projection,
        )

    def test_storage_projection_is_read_only_scheduler_projection(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]

        projection = (
            root
            / "src"
            / "dairyos"
            / "api"
            / "feed_inventory_projection.py"
        ).read_text(
            encoding="utf-8",
        )

        self.assertNotIn(
            "sync_tmr_feed_storage(",
            projection,
        )

        self.assertIn(
            '"authority": "RUNTIME_SCHEDULER"',
            projection,
        )

        self.assertIn(
            '"write_on_get": False',
            projection,
        )

    def test_unstocked_tmr_items_do_not_create_negative_history(self):
        self.assertIn(
            "has_storage_authority",
            self.feed,
        )
        self.assertIn(
            "has_finance_stock_authority",
            self.feed,
        )
        self.assertIn(
            "has_positive_manual_stock_authority",
            self.feed,
        )

    def test_finance_remains_purchase_authority(self):
        self.assertIn(
            "purchased_from_finance",
            self.projection,
        )
        self.assertIn(
            "FINANCE_FEED",
            self.projection,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
