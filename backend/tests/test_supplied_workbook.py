from pathlib import Path
from unittest import TestCase

from app.parser import parse_workbook
from app.pdfs import build_work_order_pdf
from app.main import app, make_outputs


class SuppliedWorkbookTests(TestCase):
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
