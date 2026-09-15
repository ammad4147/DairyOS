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
        self.assertIn("def _finance_price_authority", self.api)

    def test_void_rows_are_excluded(self):
        self.assertIn("if not is_active(row):", self.api)

    def test_only_feed_purchase_rows_can_price_tmr(self):
        self.assertIn('{"EXPENSE", "PAYMENT", "PURCHASE"}', self.api)
        self.assertIn("_finance_feed_item_name(row)", self.api)

    def test_latest_price_orders_by_date_then_transaction_id(self):
        self.assertIn('int(getattr(row, "id", 0) or 0)', self.api)
        self.assertIn('existing["sort_key"] >= key', self.api)

    def test_finance_price_requires_positive_rate(self):
        self.assertIn("if rate <= 0:", self.api)

    def test_price_source_is_persisted_with_tmr_version(self):
        self.assertIn('price_source: str = Field(default="FINANCE")', self.api)
        self.assertIn('"price_source": selected_source', self.api)
        self.assertIn('price_source must be FINANCE or MANUAL', self.api)

    def test_manual_override_can_supersede_available_finance_price(self):
        self.assertIn('if selected_source == "MANUAL":', self.api)
        self.assertIn('effective_source = "MANUAL"', self.api)
        self.assertIn('rate = manual_rate', self.api)
        self.assertIn('"selected_price_source": selected_source', self.api)

    def test_finance_reference_remains_exposed_when_manual_is_selected(self):
        self.assertIn('"finance_price_per_kg"', self.api)
        self.assertIn('"finance_transaction_id"', self.api)
        self.assertIn('"finance_purchase_date"', self.api)

    def test_manual_fallback_remains_when_finance_has_no_price(self):
        self.assertIn('"MANUAL_FALLBACK"', self.api)
        self.assertIn("fallback_price_per_kg", self.api)

    def test_tmr_ui_reads_single_governed_summary(self):
        self.assertIn("fetch(`${API_BASE}/farm/tmr`)", self.ui)
        self.assertNotIn("/farm/feed-inventory/authoritative", self.ui)

    def test_tmr_ui_has_explicit_finance_or_manual_selector(self):
        self.assertIn("Price Source", self.ui)
        self.assertIn('<option value="FINANCE"', self.ui)
        self.assertIn('<option value="MANUAL">Manual</option>', self.ui)
        self.assertIn("setSource", self.ui)

    def test_manual_price_is_editable_when_manual_is_selected(self):
        self.assertIn("Manual Price", self.ui)
        self.assertIn("setManual", self.ui)
        self.assertIn("r.selected_price_source==='MANUAL'", self.ui)

    def test_selected_price_source_is_saved_by_ui(self):
        self.assertIn("price_source:x.selected_price_source", self.ui)
        self.assertIn("fallback_price_per_kg:Number(x.manual_price_per_kg", self.ui)

    def test_finance_provenance_remains_visible_to_operator(self):
        self.assertIn("finance_transaction_id", self.ui)
        self.assertIn("finance_purchase_date", self.ui)
        self.assertIn("Finance reference", self.ui)


if __name__ == "__main__":
    unittest.main(verbosity=2)
