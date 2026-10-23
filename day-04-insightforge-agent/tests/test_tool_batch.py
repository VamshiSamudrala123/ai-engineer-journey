
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

project_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from tool_batch import run_tool_batch


def fake_call(name, arguments=None):
    return SimpleNamespace(
        name=name,
        args=arguments or {},
    )


class TestToolBatch(unittest.TestCase):

    @patch("tool_batch.execute_tool")
    def test_multiple_tools(self, mock_execute):
        mock_execute.side_effect = [
            {"transaction_count": 100},
            [{"payment_format": "ACH"}],
        ]

        calls = [
            fake_call("inspect_banking_data"),
            fake_call("analyze_payment_formats", {"top_n": 5}),
        ]

        parts, trace = run_tool_batch(calls)

        self.assertEqual(len(parts), 2)
        self.assertEqual(len(trace), 2)
        self.assertEqual(mock_execute.call_count, 2)

        self.assertEqual(
            parts[0].function_response.name,
            "inspect_banking_data",
        )

        self.assertEqual(
            parts[1].function_response.name,
            "analyze_payment_formats",
        )

        self.assertEqual(trace[0]["status"], "success")

    @patch("tool_batch.execute_tool")
    def test_unknown_tool_rejected(self, mock_execute):
        calls = [
            fake_call("delete_all_transactions")
        ]

        with self.assertRaises(ValueError):
            run_tool_batch(calls)

        mock_execute.assert_not_called()

    
    
    @patch("tool_batch.execute_tool")
    def test_invalid_arguments_return_safe_error(self, mock_execute):
        mock_execute.side_effect = ValueError(
            "Sensitive internal error details"
        )

        calls = [
            fake_call("analyze_payment_formats", {"top_n": 0})
        ]

        parts, trace = run_tool_batch(calls)

        self.assertEqual(len(parts), 1)
        self.assertEqual(trace[0]["status"], "error")

        payload = parts[0].function_response.response

        self.assertEqual(
            payload["error"]["code"],
            "INVALID_ARGUMENTS",
        )

        self.assertNotIn(
            "Sensitive internal error details",
            str(payload),
        )

    @patch("tool_batch.execute_tool")
    def test_too_many_calls_rejected(self, mock_execute):
        calls = [
            fake_call("inspect_banking_data")
            for _ in range(4)
        ]

        with self.assertRaises(ValueError):
            run_tool_batch(calls)

        mock_execute.assert_not_called()

if __name__ == "__main__":
    unittest.main()
