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
        self.assertIn("unit_rate: hasRevenueField('rate') && revRate ? Number(revRate) : null", self.source)
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
            "Transaction #",
            self.ledger,
        )

        self.assertIn(
            "Unit Rate",
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
            "'Transaction #'",
            "'Date'",
            "'Item / Category'",
            "'Quantity'",
            "'Unit'",
            "'Unit Rate'",
            "'Amount'",
            "'Buyer / Customer'",
            "'Payment Method'",
            "'Reference'",
            "'Status'",
            "'Due Date'",
            "'Settled Date'",
            "'Animal / Other Details'",
            "'Notes'",
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
            "<th>Transaction #</th>",
            "<th>Date</th>",
            "<th>Item / Category</th>",
            "Quantity",
            "Unit",
            "Unit Rate",
            "Amount",
            "<th>Buyer / Customer</th>",
            "<th>Payment Method</th>",
            "<th>Reference</th>",
            "<th>Status</th>",
            "<th>Due Date</th>",
            "<th>Settled Date</th>",
            "<th>Animal / Other Details</th>",
            "<th>Notes</th>",
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
            "const ledgerQuantityValue =",
            self.source,
        )

        self.assertIn(
            "return qty > 0 ? qty.toLocaleString('en-PK', { maximumFractionDigits: 3 }) : '—';",
            self.source,
        )

        self.assertIn(
            "? 'litres'",
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

    def test_ledger_print_does_not_depend_on_popup_permission(self):
        """Regression for the observed blocked-ledger-print operator message."""
        self.assertIn("const printLedgerSurface =", self.source)
        for marker in ("const printRevenueLedger=", "const printLedger="):
            start = self.source.index(marker)
            end = self.source.find("\n  const ", start + len(marker))
            printable = self.source[start:] if end == -1 else self.source[start:end]
            self.assertIn("printLedgerSurface(", printable)
            self.assertNotIn("printWindow", printable)
            self.assertNotIn("printFrame", printable)
            self.assertNotIn("window.open('', '_blank'", printable)

        self.assertIn("window.print()", self.source)
        self.assertIn("afterprint", self.source)
        self.assertIn("dairyos-ledger-print-surface", self.source)
        self.assertNotIn("document.createElement('iframe')", self.source)
        self.assertNotIn("printWindow.print()", self.source)

    def test_expense_and_explorer_show_complete_financial_fields(self):
        for label in (
            "Transaction #",
            "Item / Specification",
            "Master Category",
            "Quantity",
            "Unit",
            "Unit Rate",
            "Amount",
            "Counterparty",
            "Payment Method",
            "Reference",
            "Status",
            "Due Date",
            "Settled Date",
            "COP / Attribution",
            "Animal / Other Details",
            "Notes",
        ):
            self.assertIn(label, self.source)

    def test_revenue_form_contract_drives_dynamic_visibility_and_payload_purge(self):
        """Each revenue intent owns its visible, required and cleared fields."""
        for marker in (
            "type RevenueFieldName",
            "type FinanceFieldContract",
            "const REVENUE_FIELD_CONTRACTS",
            "const hasRevenueField",
            "const requiresRevenueField",
            "const clears = new Set(revenueContract.clearsOnExit);",
            "required={requiresRevenueField('quantity')}",
            "required={requiresRevenueField('rate')}",
            "required={requiresRevenueField('amount')}",
            "required={requiresRevenueField('animalId')}",
        ):
            self.assertIn(marker, self.source)

        self.assertIn(
            "'Organic Manure / Dung': { visible: ['amount']",
            self.source,
        )
        self.assertIn(
            "'Milking Animal Sale': { visible: ['animalId', 'amount']",
            self.source,
        )
        self.assertIn(
            "quantity: isAnimalSale ? 1 : hasRevenueField('quantity')",
            self.source,
        )
        self.assertIn(
            "unit_rate: hasRevenueField('rate')",
            self.source,
        )
        self.assertNotIn(
            'aria-label="Animal sale quantity"',
            self.source,
        )

    def test_expense_edit_form_is_contextual_and_keeps_intent_fixed(self):
        for marker in (
            "const editIsAnimalPurchase",
            "const editIsSemenPurchase",
            "const editRequiresCustomSpecification",
            "const editCopEnabled",
            "The authoritative expense category is fixed for this edit.",
            'name="animal_category" value={editTarget.animal_category || \'\'} readOnly',
        ):
            self.assertIn(marker, self.source)

        self.assertIn(
            "const amount = editIsAnimalPurchase ? Number(form.get('amount') || 0) : qty > 0 ? qty * rate",
            self.source,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
