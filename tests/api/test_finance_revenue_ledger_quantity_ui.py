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


class FinanceRevenueLedgerQuantityContractTest(
    unittest.TestCase
):

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

    def test_milk_sale_form_uses_quantity_and_rate_with_readonly_amount(self):
        self.assertIn("const [revRate, setRevRate] = useState('');", self.source)
        self.assertIn("const calculatedMilkSaleAmount", self.source)
        self.assertIn('placeholder="Quantity (Litres)"', self.source)
        self.assertIn('placeholder="Rate / Litre"', self.source)
        self.assertIn("Amount — auto calculated from Quantity × Rate", self.source)
        self.assertIn("readOnly value={calculatedMilkSaleAmount", self.source)
        self.assertIn("unit_rate: isMilkSale ? Number(revRate) : null", self.source)
        self.assertIn("amount: isMilkSale ? undefined : amount", self.source)

    def test_screen_uses_readable_revenue_table(self):
        self.assertIn(
            "<table",
            self.ledger,
        )

        self.assertIn(
            "Buyer / Customer",
            self.ledger,
        )

        self.assertIn(
            "Quantity",
            self.ledger,
        )

        self.assertIn(
            "Actions",
            self.ledger,
        )

    def test_screen_uses_revenue_specific_exports(self):
        self.assertIn(
            "saveRevenueLedgerCsv(",
            self.ledger,
        )

        self.assertIn(
            "printRevenueLedger(",
            self.ledger,
        )

    def test_csv_has_same_revenue_columns(self):
        csv_start = self.source.index(
            "const saveRevenueLedgerCsv="
        )

        csv_end = self.source.index(
            "const saveLedgerCsv=",
            csv_start,
        )

        csv = self.source[
            csv_start:csv_end
        ]

        for label in (
            "'Date'",
            "'Particulars'",
            "'Quantity'",
            "'Buyer / Customer'",
            "'Reference'",
            "'Status'",
            "'Amount'",
        ):
            self.assertIn(
                label,
                csv,
            )

        self.assertNotIn(
            "'Master Category'",
            csv,
        )

        self.assertNotIn(
            "'Type'",
            csv,
        )

    def test_print_has_same_revenue_columns(self):
        print_start = self.source.index(
            "const printRevenueLedger="
        )

        print_end = self.source.index(
            "const printLedger=",
            print_start,
        )

        printable = self.source[
            print_start:print_end
        ]

        for label in (
            "<th>Date</th>",
            "<th>Particulars</th>",
            "Quantity",
            "<th>Buyer / Customer</th>",
            "<th>Reference</th>",
            "<th>Status</th>",
            "Amount",
        ):
            self.assertIn(
                label,
                printable,
            )

        self.assertNotIn(
            "<th>Master Category</th>",
            printable,
        )

        self.assertNotIn(
            "<th>Type</th>",
            printable,
        )

    def test_milk_sales_display_quantity_as_litres(self):
        self.assertIn(
            "const ledgerQuantity=",
            self.source,
        )

        self.assertIn(
            "return `${formatted} L`;",
            self.source,
        )

    def test_revenue_codes_are_operator_readable(self):
        self.assertIn(
            "MILK_SALES:'Milk Sales'",
            self.source,
        )

        self.assertIn(
            "MALE_CALF_SALE:'Male Calf Sale'",
            self.source,
        )

        self.assertIn(
            "{revenueParticulars(r)}",
            self.ledger,
        )

    def test_animal_sale_displays_animal_id(self):
        self.assertIn(
            "const revenueAnimalId=",
            self.source,
        )

        self.assertIn(
            "Animal #{animalId}",
            self.ledger,
        )

    def test_month_caption_is_clear(self):
        self.assertIn(
            "Current month:",
            self.ledger,
        )

        self.assertNotIn(
            "Current month ?",
            self.ledger,
        )

    def test_generic_exports_are_preserved(self):
        self.assertIn(
            "const saveLedgerCsv=",
            self.source,
        )

        self.assertIn(
            "const printLedger=",
            self.source,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
