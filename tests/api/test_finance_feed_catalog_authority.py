import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

FINANCE = (
    ROOT
    / "src"
    / "dairyos"
    / "api"
    / "finance_ledger.py"
)

FEED = (
    ROOT
    / "src"
    / "dairyos"
    / "api"
    / "feed_inventory.py"
)


class FinanceFeedCatalogAuthorityContractTest(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.finance = FINANCE.read_text(encoding="utf-8")
        cls.feed = FEED.read_text(encoding="utf-8")

    def test_finance_has_feed_catalog_sync_helper(self):
        self.assertIn(
            "def _ensure_feed_catalog_authority(",
            self.finance,
        )

    def test_finance_create_calls_sync_before_commit(self):
        create_start = self.finance.index(
            "def create_finance_ledger_entry("
        )

        create_end = self.finance.index(
            '@router.get("/taxonomy")',
            create_start,
        )

        block = self.finance[
            create_start:create_end
        ]

        sync_pos = block.index(
            "_ensure_feed_catalog_authority("
        )

        commit_pos = block.index(
            "session.commit()"
        )

        self.assertLess(sync_pos, commit_pos)

    def test_catalog_sync_does_not_create_purchase_movement(self):
        helper_start = self.finance.index(
            "def _ensure_feed_catalog_authority("
        )

        helper_end = self.finance.index(
            "def _linked_milk_sale(",
            helper_start,
        )

        helper = self.finance[
            helper_start:helper_end
        ]

        self.assertIn(
            "FeedInventoryItem(",
            helper,
        )

        self.assertNotIn(
            "InventoryTransaction(",
            helper,
        )

        self.assertNotIn(
            'movement_type="PURCHASE"',
            helper,
        )

    def test_catalog_sync_uses_shared_session_not_committing_repo_add(self):
        helper_start = self.finance.index(
            "def _ensure_feed_catalog_authority("
        )

        helper_end = self.finance.index(
            "def _linked_milk_sale(",
            helper_start,
        )

        helper = self.finance[
            helper_start:helper_end
        ]

        self.assertIn(
            "factory.session.add(row)",
            helper,
        )

        self.assertIn(
            "factory.session.flush()",
            helper,
        )

        self.assertNotIn(
            "repository.add(",
            helper,
        )

        self.assertNotIn(
            "session.commit()",
            helper,
        )

    def test_existing_catalog_is_reused(self):
        self.assertIn(
            "existing = repository.get_by_item(item_name)",
            self.finance,
        )

        self.assertIn(
            "if existing is not None:",
            self.finance,
        )

    def test_unit_mismatch_is_rejected(self):
        self.assertIn(
            "Feed catalog unit mismatch",
            self.finance,
        )

    def test_inactive_catalog_can_be_reactivated(self):
        self.assertIn(
            "if not existing.active:",
            self.finance,
        )

        self.assertIn(
            "existing.active = True",
            self.finance,
        )

    def test_void_quantity_authority_remains_is_active_guarded(self):
        purchase_start = self.feed.index(
            "def _finance_purchase_rows("
        )

        purchase_end = self.feed.index(
            "def _finance_purchased_quantity(",
            purchase_start,
        )

        block = self.feed[
            purchase_start:purchase_end
        ]

        self.assertIn(
            "if is_active(row)",
            block,
        )

    def test_custom_other_feed_uses_custom_specification(self):
        self.assertIn(
            'if sub == "Other":',
            self.finance,
        )

        self.assertIn(
            "custom_specification",
            self.finance,
        )

        self.assertIn(
            "def _finance_feed_item_name(row):",
            self.feed,
        )

        self.assertIn(
            "_finance_feed_item_name(row) == item",
            self.feed,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
