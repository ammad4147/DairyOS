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
REPORTING_TAB = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "ReportingTab.tsx"
)


class FinanceRevenueLedgerQuantityContractTest(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.source = FINANCE_TAB.read_text(
            encoding="utf-8",
        )
        cls.reporting = REPORTING_TAB.read_text(
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

    def test_finance_tab_does_not_offer_report_outputs(self):
        self.assertNotIn("saveRevenueLedgerCsv(", self.ledger)
        self.assertNotIn("printRevenueLedger(", self.ledger)
        self.assertNotIn("Save CSV", self.source)
        self.assertNotIn("window.print()", self.source)
        self.assertNotIn("dairyos-ledger-print-surface", self.source)

    def test_settings_reporting_owns_finance_outputs(self):
        self.assertIn("Transaction Ledger", self.reporting)
        self.assertIn("Income and Expense Summary", self.reporting)
        self.assertIn("Finance", self.reporting)
        self.assertIn("Save {format}", self.reporting)
        self.assertIn("Print", self.reporting)

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

    def test_finance_reporting_does_not_depend_on_popup_permission(self):
        self.assertIn("const printReport = () =>", self.reporting)
        self.assertIn("window.print()", self.reporting)
        self.assertNotIn("window.open('', '_blank'", self.reporting)

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
