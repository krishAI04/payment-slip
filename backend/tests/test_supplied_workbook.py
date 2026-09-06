from decimal import Decimal
from pathlib import Path
from unittest import TestCase

from app.parser import parse_workbook
from app.pdfs import build_work_order_pdf, currency
from app.main import app, make_outputs


class SuppliedWorkbookTests(TestCase):
    def test_pdf_amounts_round_to_whole_rupees(self):
        self.assertEqual(currency(Decimal("1326.49")), "Rs. 1,326")
        self.assertEqual(currency(Decimal("1326.50")), "Rs. 1,327")

    def test_groups_records_and_builds_pdf(self):
        sample = Path(r"C:\Users\hp\Downloads\july-2026.xlsx")
        if not sample.exists():
            self.skipTest("The supplied sample workbook is unavailable.")
        slips = parse_workbook(sample.read_bytes())
        self.assertEqual(len(slips), 127)
        selected = [slip for slip in slips if slip.work_order == "HR/TSW/2526/0566"]
        self.assertEqual(len(selected), 6)
        self.assertTrue(build_work_order_pdf(selected).startswith(b"%PDF"))
        outputs = make_outputs(slips)
        self.assertEqual(len(outputs), 10)
        self.assertTrue(all(pdf.startswith(b"%PDF") for pdf in outputs.values()))

    def test_na_deduction_totals_are_treated_as_zero(self):
        sample = Path(r"C:\Users\hp\Downloads\Book1.xlsx")
        if not sample.exists():
            self.skipTest("The supplied Book1 workbook is unavailable.")
        slips = parse_workbook(sample.read_bytes())
        supervisor = next(slip for slip in slips if slip.employee == "PRIYANSHU VISHWAKARMA")
        self.assertEqual(supervisor.total_deduction, Decimal("0"))
