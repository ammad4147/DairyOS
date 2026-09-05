import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
TMR = ROOT / "src/dairyos/api/tmr.py"
COML = ROOT / "src/dairyos/api/coml.py"
FINANCE = ROOT / "src/dairyos/api/finance_ledger.py"
APP = ROOT / "src/dairyos/app.py"


class TmrCopAuthorityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmr = TMR.read_text(encoding="utf-8")
        cls.coml = COML.read_text(encoding="utf-8")
        cls.finance = FINANCE.read_text(encoding="utf-8")
        cls.app = APP.read_text(encoding="utf-8")

    def test_six_dairyos_categories_are_mapped(self):
        for value in (
            '"Milking": ["early_milking", "mid_milking", "late_milking"]',
            '"Dry": ["far_off", "close_up"]',
            '"Heifer": ["heifer_growth"]',
            '"Female Calf": ["calf_starter"]',
            '"Male Calf": ["calf_starter"]',
            '"Bull": ["bull"]',
        ):
            self.assertIn(value, self.tmr)

    def test_bull_ration_is_present(self):
        self.assertIn(
            '"bull": [15, 3, 4, 0.5, 0.5, 0, 100, 50, 0, 30, 0]',
            self.tmr,
        )

    def test_category_cost_uses_arithmetic_mean(self):
        self.assertIn(
            "head_cost = sum(values) / len(values) if values else 0.0",
            self.tmr,
        )

    def test_active_herd_counts_drive_daily_cost(self):
        self.assertIn("factory.animal().active_animals()", self.tmr)
        self.assertIn('"category_cost_per_day"', self.tmr)
        self.assertIn('"total_herd_feed_cost_per_day"', self.tmr)


    def test_active_herd_category_normalization_matches_herd_register(self):
        from dairyos.api.tmr import _normalize_herd_category

        cases = [
            (dict(lifecycle_status="LACTATING", sex="FEMALE", is_currently_milking=True), "Milking"),
            (dict(lifecycle_status="DRY", sex="FEMALE", is_currently_milking=False), "Dry"),
            (dict(lifecycle_status="HEIFER", sex="FEMALE", is_currently_milking=False), "Heifer"),
            (dict(lifecycle_status="CLOSE_UP", sex="FEMALE", is_currently_milking=False), "Heifer"),
            (dict(lifecycle_status="CALF", sex="FEMALE", is_currently_milking=False), "Female Calf"),
            (dict(lifecycle_status="CALF", sex="MALE", is_currently_milking=False), "Male Calf"),
            (dict(lifecycle_status="BULL", sex="MALE", is_currently_milking=False), "Bull"),
        ]

        for values, expected in cases:
            animal = SimpleNamespace(animal_type="CATTLE", **values)
            self.assertEqual(_normalize_herd_category(animal), expected)

    def test_finance_price_authority_excludes_void(self):
        self.assertIn("if not is_active(row):", self.tmr)
        self.assertIn('"price_source": (', self.tmr)
        self.assertIn('"FINANCE"', self.tmr)

    def test_weekly_vet_endorsement_is_append_only(self):
        self.assertIn('ENDORSEMENT_GROUP = "TMR_WEEKLY_ENDORSEMENT"', self.tmr)
        self.assertIn("factory.feed_rations().add(record)", self.tmr)
        self.assertNotIn(".delete(", self.tmr)

    def test_weekly_advisory_is_derived_every_week(self):
        self.assertIn('"status": "ENDORSED" if latest else "DUE"', self.tmr)
        self.assertIn("Vet review due:", self.tmr)

    def test_period_feed_cost_uses_weekly_snapshot_and_live_today(self):
        self.assertIn('basis = "LIVE_TMR"', self.tmr)
        self.assertIn('basis = "WEEKLY_VET_ENDORSED_TMR"', self.tmr)
        self.assertIn('"UNENDORSED_LIVE_TMR_FALLBACK"', self.tmr)

    def test_coml_feed_branch_comes_from_tmr(self):
        integrated = self.coml[self.coml.index('@router.get("/integrated")'):]
        self.assertIn("tmr_feed_cost_for_period(", integrated)
        self.assertIn('"TMR_HERD_COST+FINANCE_OPEX"', integrated)
        self.assertNotIn("feed_total += amount", integrated)

    def test_coml_still_uses_finance_opex(self):
        integrated = self.coml[
            self.coml.index('@router.get("/integrated")'):
        ]

        self.assertIn(
            'master == "OPEX"',
            integrated,
        )

        self.assertIn(
            "factory.finance().get_all()",
            integrated,
        )

        self.assertIn(
            "is_expense(item)",
            integrated,
        )

        self.assertIn(
            'status == "VOID"',
            integrated,
        )

        self.assertIn(
            "opex_total += amount",
            integrated,
        )

        self.assertIn(
            '"TMR_HERD_COST+FINANCE_OPEX"',
            integrated,
        )

    def test_finance_taxonomy_exposes_tmr_catalog_and_other(self):
        self.assertIn("tmr_default_catalog_names()", self.finance)
        self.assertIn("is_tmr_catalog_row(row)", self.finance)
        self.assertIn('if "Other" in feed_items:', self.finance)

    def test_finance_validation_accepts_governed_tmr_catalog_only(self):
        self.assertIn("def _is_governed_tmr_feed_item(", self.finance)
        self.assertIn("_is_governed_tmr_feed_item(entry.sub_category)", self.finance)

    def test_finance_edit_also_ensures_feed_catalog(self):
        start = self.finance.index("def edit_finance_ledger_entry(")
        block = self.finance[start:self.finance.index("\n@router.", start)]
        self.assertIn("_ensure_feed_catalog_authority(", block)

    def test_tmr_router_is_registered(self):
        self.assertIn(
            "from dairyos.api.tmr import router as tmr_router",
            self.app,
        )
        self.assertIn("app.include_router(tmr_router)", self.app)


if __name__ == "__main__":
    unittest.main(verbosity=2)
