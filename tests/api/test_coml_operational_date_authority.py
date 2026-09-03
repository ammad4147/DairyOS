from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]

TMR = (
    ROOT
    / "src"
    / "dairyos"
    / "api"
    / "tmr.py"
)

COML = (
    ROOT
    / "src"
    / "dairyos"
    / "api"
    / "coml.py"
)


class ComlOperationalDateAuthorityContractTest(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.tmr = TMR.read_text(
            encoding="utf-8",
        )

        cls.coml = COML.read_text(
            encoding="utf-8",
        )

    def test_tmr_future_only_period_is_zero(self):
        self.assertIn(
            "if start > today:",
            self.tmr,
        )

        self.assertIn(
            '"total_feed_cost": 0.0',
            self.tmr,
        )

        self.assertIn(
            '"daily": []',
            self.tmr,
        )

    def test_tmr_loop_stops_at_operational_date(self):
        self.assertIn(
            "effective_end = min(",
            self.tmr,
        )

        self.assertIn(
            "while day <= effective_end:",
            self.tmr,
        )

        self.assertNotIn(
            "while day <= end:",
            self.tmr,
        )

    def test_tmr_exposes_clamp_metadata(self):
        self.assertIn(
            '"requested_period": {',
            self.tmr,
        )

        self.assertIn(
            '"effective_period":',
            self.tmr,
        )

        self.assertIn(
            '"operational_date":',
            self.tmr,
        )

        self.assertIn(
            '"clamped_to_operational_date"',
            self.tmr,
        )

    def test_coml_default_month_uses_operational_date(self):
        self.assertIn(
            "today.replace(day=1)",
            self.coml,
        )

    def test_coml_has_requested_and_effective_period(self):
        self.assertIn(
            "requested_end = (",
            self.coml,
        )

        self.assertIn(
            "effective_end = (",
            self.coml,
        )

        self.assertIn(
            "requested_end,",
            self.coml,
        )

        self.assertIn(
            "today,",
            self.coml,
        )

    def test_milk_uses_effective_end(self):
        normalized = "".join(
            self.coml.split()
        )

        self.assertIn(
            "milk_litres_for_period("
            "factory,start,effective_end,)",
            normalized,
        )

    def test_finance_opex_uses_effective_end(self):
        self.assertIn(
            "<= effective_end",
            self.coml,
        )

        self.assertIn(
            "factory.finance().get_all()",
            self.coml,
        )

    def test_void_finance_rows_are_excluded(self):
        self.assertIn(
            'status == "VOID"',
            self.coml,
        )

    def test_equipment_purchase_uses_item_not_row(self):
        self.assertIn(
            '"sub_category"',
            self.coml,
        )

        self.assertNotIn(
            'getattr(row, "sub_category"',
            self.coml,
        )

        normalized = "".join(
            self.coml.split()
        )

        self.assertIn(
            'getattr(item,"sub_category","",)',
            normalized,
        )

    def test_equipment_purchase_is_excluded_from_cop(self):
        self.assertIn(
            '== "Equipment Purchase"',
            self.coml,
        )

    def test_finance_opex_is_still_authoritative(self):
        self.assertIn(
            'master == "OPEX"',
            self.coml,
        )

        self.assertIn(
            "opex_total += amount",
            self.coml,
        )

        self.assertIn(
            '"TMR_HERD_COST+FINANCE_OPEX"',
            self.coml,
        )

    def test_response_exposes_clamp_metadata(self):
        self.assertIn(
            '"effective_period": (',
            self.coml,
        )

        self.assertIn(
            '"operational_date": (',
            self.coml,
        )

        self.assertIn(
            '"clamped_to_operational_date": (',
            self.coml,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
