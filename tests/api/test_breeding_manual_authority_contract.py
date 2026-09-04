"""Contracts for manual-authority breeding workflow governance.

DairyOS may calculate biological clocks for reminders and guidance, but it
must not use those clocks as the source of truth for biological events. Manual
Passport/breeding entries are the controller for insemination and downstream
workflow progression.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
BREEDING_API = ROOT / "src" / "dairyos" / "api" / "breeding_biology.py"
BREEDING_UI = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "BreedingTab.tsx"
)


class BreedingManualAuthorityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_source = BREEDING_API.read_text(encoding="utf-8")
        cls.ui_source = BREEDING_UI.read_text(encoding="utf-8")

    def test_insemination_runtime_excludes_bulls_and_calves_only_by_lifecycle_boundary(self):
        self.assertIn('_AI_LIFECYCLES = {"HEIFER", "LACTATING", "DRY"}', self.api_source)
        self.assertIn("Only female animals can enter the breeding workflow.", self.api_source)
        self.assertIn("Female calves cannot enter the breeding workflow.", self.api_source)
        self.assertIn("female calves, male calves, bulls", self.api_source)

    def test_biological_clock_does_not_block_manual_insemination_entry(self):
        self.assertNotIn("state.eligible_to_breed", self.api_source)
        self.assertNotIn("not yet biologically eligible for insemination", self.api_source)
        self.assertIn("Biological clocks, waiting periods, and readiness calculations are", self.api_source)
        self.assertIn("A manual operator breeding entry is the authority.", self.api_source)

    def test_frontend_ai_selector_uses_manual_category_filter_not_readiness_decision(self):
        self.assertIn("const aiSelectableCategory", self.ui_source)
        self.assertIn("manualAiAnimals = useMemo", self.ui_source)
        self.assertIn("const aiCandidates = useMemo", self.ui_source)
        self.assertIn("Milking, Dry and Heifer only; active cycles excluded", self.ui_source)
        self.assertNotIn("Boolean(s?.eligible_to_breed)&&", self.ui_source)
        self.assertNotIn("No mature female animals currently eligible for insemination", self.ui_source)

    def test_operator_authority_copy_is_visible_without_changing_capabilities(self):
        self.assertIn("operator-entered breeding events as authoritative Passport records", self.ui_source)
        self.assertIn("Biological clocks provide reminders and guidance only", self.ui_source)
        self.assertIn("Manual AI authority", self.ui_source)
        self.assertIn("operator entry remains authoritative", self.ui_source)
        self.assertIn("Save Breeding Entry", self.ui_source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
