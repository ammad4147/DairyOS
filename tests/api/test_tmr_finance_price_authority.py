from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
TMR_API = ROOT / "src" / "dairyos" / "api" / "tmr.py"
TMR_UI = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "TMRPreparationTool.tsx"
)


class TmrFinancePriceAuthorityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = TMR_API.read_text(encoding="utf-8")
        cls.ui = TMR_UI.read_text(encoding="utf-8")

    def test_finance_price_authority_is_backend_governed(self):
        self.assertIn(
            "def _finance_price_authority",
            self.api,
        )

    def test_void_rows_are_excluded(self):
        self.assertIn(
            "if not is_active(row):",
            self.api,
        )

    def test_only_feed_purchase_rows_can_price_tmr(self):
        self.assertIn(
            '{"EXPENSE", "PAYMENT", "PURCHASE"}',
            self.api,
        )
        self.assertIn(
            "_finance_feed_item_name(row)",
            self.api,
        )

    def test_latest_price_orders_by_date_then_transaction_id(self):
        self.assertIn(
            "int(getattr(row, \"id\", 0) or 0)",
            self.api,
        )
        self.assertIn(
            'existing["sort_key"] >= key',
            self.api,
        )

    def test_finance_price_requires_positive_rate(self):
        self.assertIn(
            "if rate <= 0:",
            self.api,
        )

    def test_priced_stage_exposes_finance_provenance(self):
        self.assertIn(
            '"price_source": (',
            self.api,
        )
        self.assertIn(
            '"FINANCE"',
            self.api,
        )
        self.assertIn(
            '"finance_transaction_id"',
            self.api,
        )
        self.assertIn(
            '"finance_purchase_date"',
            self.api,
        )

    def test_manual_fallback_remains_when_finance_has_no_price(self):
        self.assertIn(
            '"MANUAL_FALLBACK"',
            self.api,
        )
        self.assertIn(
            "fallback_price_per_kg",
            self.api,
        )

    def test_tmr_ui_reads_single_governed_summary(self):
        self.assertIn(
            "fetch(`${API_BASE}/farm/tmr`)",
            self.ui,
        )
        self.assertNotIn(
            "/farm/feed-inventory/authoritative",
            self.ui,
        )

    def test_finance_price_is_read_only_in_tmr_ui(self):
        self.assertIn(
            "row.price_source",
            self.ui,
        )
        self.assertIn(
            "disabled={",
            self.ui,
        )
        self.assertIn(
            "=== 'FINANCE'",
            self.ui,
        )

    def test_finance_provenance_is_visible_to_operator(self):
        self.assertIn(
            "finance_transaction_id",
            self.ui,
        )
        self.assertIn(
            "finance_purchase_date",
            self.ui,
        )
        self.assertIn(
            "Finance",
            self.ui,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
