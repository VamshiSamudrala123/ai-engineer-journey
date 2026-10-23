
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Allow tests to import modules from the Project 04 folder.
project_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

import tool_registry


class TestToolRegistry(unittest.TestCase):

    @patch("tool_registry.inspect_banking_data")
    def test_inspect_dataset(self, mock_inspect):
        mock_inspect.return_value = {"transaction_count": 100}

        result = tool_registry.execute_tool(
            "inspect_banking_data"
        )

        self.assertEqual(result["transaction_count"], 100)
        mock_inspect.assert_called_once_with(
            tool_registry.TRANSACTIONS,
            tool_registry.ACCOUNTS,
        )

    @patch("tool_registry.analyze_payment_formats")
    def test_payment_analysis_default_limit(self, mock_analyze):
        mock_analyze.return_value = []

        tool_registry.execute_tool("analyze_payment_formats")

        mock_analyze.assert_called_once_with(
            tool_registry.TRANSACTIONS,
            top_n=10,
        )

    @patch("tool_registry.analyze_payment_formats")
    def test_payment_analysis_custom_limit(self, mock_analyze):
        mock_analyze.return_value = []

        tool_registry.execute_tool(
            "analyze_payment_formats",
            {"top_n": 5},
        )

        mock_analyze.assert_called_once_with(
            tool_registry.TRANSACTIONS,
            top_n=5,
        )

    @patch("tool_registry.investigate_account")
    def test_account_investigation(self, mock_investigate):
        mock_investigate.return_value = {
            "total_transactions": 3
        }

        result = tool_registry.execute_tool(
            "investigate_account",
            {
                "bank_id": 3208,
                "account_number": "8000F4580",
            },
        )

        self.assertEqual(result["total_transactions"], 3)

        mock_investigate.assert_called_once_with(
            tool_registry.TRANSACTIONS,
            bank_id=3208,
            account_number="8000F4580",
        )

    def test_unknown_tool_rejected(self):
        with self.assertRaises(ValueError):
            tool_registry.execute_tool(
                "delete_all_transactions"
            )

    def test_arguments_must_be_dictionary(self):
        with self.assertRaises(ValueError):
            tool_registry.execute_tool(
                "inspect_banking_data",
                ["unexpected"],
            )

    def test_unexpected_arguments_rejected(self):
        with self.assertRaises(ValueError):
            tool_registry.execute_tool(
                "inspect_banking_data",
                {"file_path": "/private/data.csv"},
            )

        with self.assertRaises(ValueError):
            tool_registry.execute_tool(
                "analyze_payment_formats",
                {"file_path": "/private/data.csv"},
            )

    def test_account_requires_exact_arguments(self):
        with self.assertRaises(ValueError):
            tool_registry.execute_tool(
                "investigate_account",
                {"bank_id": 3208},
            )

        with self.assertRaises(ValueError):
            tool_registry.execute_tool(
                "investigate_account",
                {
                    "bank_id": 3208,
                    "account_number": "8000F4580",
                    "file_path": "/private/data.csv",
                },
            )


if __name__ == "__main__":
    unittest.main()
