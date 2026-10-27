"""Tests for the approved banking-tool-to-PDF reporting pipeline."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from report_service import generate_account_report


class TestReportService(unittest.TestCase):
    def setUp(self):
        self.investigation = {
            "bank_id": 3208,
            "account_number": "8000F4580",
            "total_transactions": 3,
            "outgoing_transactions": 3,
            "incoming_transactions": 0,
            "self_transfers": 0,
            "labeled_transactions": 0,
        }

    @patch("report_service.execute_tool")
    def test_uses_approved_tool_and_builds_pdf(self, mock_tool):
        mock_tool.return_value = self.investigation
        pdf = generate_account_report(3208, " 8000F4580 ")

        mock_tool.assert_called_once_with(
            "investigate_account",
            {"bank_id": 3208, "account_number": "8000F4580"},
        )
        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertGreater(len(pdf), 1500)

    @patch("report_service.execute_tool")
    def test_rejects_bad_input_before_querying(self, mock_tool):
        for bank, account in (
            (True, "8000F4580"),
            (-1, "8000F4580"),
            ("3208", "8000F4580"),
            (3208, ""),
            (3208, " " * 4),
            (3208, "X" * 65),
            (3208, None),
        ):
            with self.subTest(bank=bank, account=account):
                with self.assertRaises(ValueError):
                    generate_account_report(bank, account)
        mock_tool.assert_not_called()

    @patch("report_service.execute_tool")
    def test_rejects_mismatched_tool_result(self, mock_tool):
        mock_tool.return_value = {**self.investigation, "bank_id": 9999}
        with self.assertRaisesRegex(ValueError, "does not match"):
            generate_account_report(3208, "8000F4580")

    @patch("report_service.execute_tool")
    def test_rejects_inconsistent_counts(self, mock_tool):
        mock_tool.return_value = {
            **self.investigation,
            "total_transactions": 4,
        }
        with self.assertRaisesRegex(ValueError, "reconcile"):
            generate_account_report(3208, "8000F4580")

    @patch("report_service.execute_tool")
    def test_missing_dataset_error_propagates(self, mock_tool):
        mock_tool.side_effect = FileNotFoundError("Missing transactions CSV")
        with self.assertRaises(FileNotFoundError):
            generate_account_report(3208, "8000F4580")


if __name__ == "__main__":
    unittest.main()
