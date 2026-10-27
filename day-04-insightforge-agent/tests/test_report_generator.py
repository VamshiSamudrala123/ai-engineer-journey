"""Unit tests for deterministic, data-backed PDF generation."""

import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from report_generator import build_account_report_pdf


class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        self.result = {
            "bank_id": 10,
            "account_number": "DEMO-001",
            "total_transactions": 4,
            "outgoing_transactions": 2,
            "incoming_transactions": 1,
            "self_transfers": 1,
            "labeled_transactions": 0,
        }

    def test_generates_pdf_bytes(self):
        report = build_account_report_pdf(self.result)
        self.assertTrue(report.startswith(b"%PDF-"))
        self.assertGreater(len(report), 1500)

    def test_allows_no_matching_transactions(self):
        result = {**self.result,
                  "total_transactions": 0,
                  "outgoing_transactions": 0,
                  "incoming_transactions": 0,
                  "self_transfers": 0}
        self.assertTrue(build_account_report_pdf(result).startswith(b"%PDF-"))

    def test_rejects_inconsistent_counts(self):
        result = {**self.result, "outgoing_transactions": 3}
        with self.assertRaisesRegex(ValueError, "reconcile"):
            build_account_report_pdf(result)

    def test_rejects_invalid_fields(self):
        for result in (
            {**self.result, "bank_id": True},
            {**self.result, "account_number": ""},
            {**self.result, "total_transactions": -1},
            {**self.result, "labeled_transactions": 5},
        ):
            with self.subTest(result=result), self.assertRaises(ValueError):
                build_account_report_pdf(result)

    def test_escapes_markup_in_account_number(self):
        result = {**self.result, "account_number": "A<&B"}
        self.assertTrue(build_account_report_pdf(result).startswith(b"%PDF-"))


if __name__ == "__main__":
    unittest.main()
