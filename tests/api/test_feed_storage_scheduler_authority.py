from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]

SCHEDULER = (
    ROOT
    / "src"
    / "dairyos"
    / "feed_storage_scheduler.py"
)

APP = (
    ROOT
    / "src"
    / "dairyos"
    / "app.py"
)

FEED = (
    ROOT
    / "src"
    / "dairyos"
    / "api"
    / "feed_inventory.py"
)

PROJECTION = (
    ROOT
    / "src"
    / "dairyos"
    / "api"
    / "feed_inventory_projection.py"
)

FEED_UI = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "FeedTab.tsx"
)


class FeedStorageSchedulerAuthorityContractTest(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.scheduler = SCHEDULER.read_text(
            encoding="utf-8",
        )
        cls.app = APP.read_text(
            encoding="utf-8",
        )
        cls.feed = FEED.read_text(
            encoding="utf-8",
        )
        cls.projection = PROJECTION.read_text(
            encoding="utf-8",
        )
        cls.feed_ui = FEED_UI.read_text(
            encoding="utf-8",
        )

    def test_reconciliation_is_reusable_factory_service(self):
        self.assertIn(
            "def reconcile_tmr_feed_storage(factory):",
            self.feed,
        )

    def test_existing_api_wrapper_is_preserved(self):
        self.assertIn(
            "def sync_tmr_feed_storage(",
            self.feed,
        )
        self.assertIn(
            "return reconcile_tmr_feed_storage(",
            self.feed,
        )

    def test_scheduler_uses_fresh_repository_factory(self):
        self.assertIn(
            "RepositoryFactory.create()",
            self.scheduler,
        )
        self.assertIn(
            "factory.close()",
            self.scheduler,
        )

    def test_scheduler_reconciles_immediately_on_start(self):
        start = self.scheduler.index(
            "def start(self)"
        )
        immediate = self.scheduler.index(
            "self._reconcile()",
            start,
        )
        thread = self.scheduler.index(
            "threading.Thread(",
            start,
        )

        self.assertLess(
            immediate,
            thread,
        )

    def test_scheduler_reconciles_periodically(self):
        self.assertIn(
            "self._stop.wait(",
            self.scheduler,
        )
        self.assertIn(
            "self.interval_seconds",
            self.scheduler,
        )

    def test_scheduler_calls_governed_reconciliation(self):
        self.assertIn(
            "reconcile_tmr_feed_storage(",
            self.scheduler,
        )

    def test_scheduler_rolls_back_failed_session(self):
        self.assertIn(
            "factory.session.rollback()",
            self.scheduler,
        )

    def test_scheduler_is_started_by_app_lifespan(self):
        self.assertIn(
            "feed_storage_scheduler.start()",
            self.app,
        )

    def test_scheduler_is_stopped_by_app_lifespan(self):
        self.assertIn(
            "feed_storage_scheduler.stop()",
            self.app,
        )

    def test_authoritative_get_does_not_write(self):
        self.assertNotIn(
            "sync_tmr_feed_storage(",
            self.projection,
        )
        self.assertNotIn(
            "reconcile_tmr_feed_storage(",
            self.projection,
        )
        self.assertIn(
            '"write_on_get": False',
            self.projection,
        )

    def test_projection_declares_runtime_scheduler_authority(self):
        self.assertIn(
            '"authority": "RUNTIME_SCHEDULER"',
            self.projection,
        )

    def test_feed_ui_says_refresh_is_read_only(self):
        self.assertIn(
            "Feed Storage refresh is",
            self.feed_ui,
        )
        self.assertIn(
            "read-only.",
            self.feed_ui,
        )

    def test_feed_ui_says_scheduler_is_page_independent(self):
        normalized = " ".join(
            self.feed_ui.split()
        )

        self.assertIn(
            "DairyOS runtime independently of this page",
            normalized,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
