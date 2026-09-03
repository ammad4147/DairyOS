import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

FINANCE_TAB = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "FinanceTab.tsx"
)


class FinanceRevenueLedgerQuantityContractTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.source = FINANCE_TAB.read_text(
            encoding="utf-8",
        )

        start = cls.source.index(
            "<span>Revenue Ledger</span>"
        )

        end = cls.source.index(
            "No revenue entries in the current calendar month.",
            start,
        )

        cls.ledger = cls.source[start:end]

    def test_revenue_ledger_has_quantity_column(self):
        self.assertIn(
            ">Quantity</span>",
            self.ledger,
        )

    def test_revenue_ledger_renders_transaction_quantity(self):
        self.assertIn(
            "{ledgerQuantity(r)}",
            self.ledger,
        )

    def test_milk_sales_display_quantity_as_litres(self):
        self.assertIn(
            "const ledgerQuantity=",
            self.source,
        )

        self.assertIn(
            "String(t.category||'').toUpperCase()==='MILK_SALES'",
            self.source,
        )

        self.assertIn(
            "return `${formatted} L`;",
            self.source,
        )

    def test_missing_quantity_has_operator_readable_value(self):
        helper_start = self.source.index(
            "const ledgerQuantity="
        )

        helper_end = self.source.index(
            "const saveLedgerCsv=",
            helper_start,
        )

        helper = self.source[
            helper_start:helper_end
        ]

        self.assertIn(
            "if(!(qty>0))return '—';",
            helper,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
