
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from google.genai import types


project_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from gemini_agent import ask_agent


def tool_response(*requests):
    """Simulate Gemini requesting one or more tools."""

    calls = [
        SimpleNamespace(name=name, args=args)
        for name, args in requests
    ]

    content = types.Content(
        role="model",
        parts=[
            types.Part(
                function_call=types.FunctionCall(
                    name=name,
                    args=args,
                )
            )
            for name, args in requests
        ],
    )

    return SimpleNamespace(
        function_calls=calls,
        candidates=[
            SimpleNamespace(content=content)
        ],
    )


def final_response(answer):
    """Simulate Gemini returning a final text answer."""

    return SimpleNamespace(
        function_calls=[],
        text=answer,
    )


class TestGeminiAgent(unittest.TestCase):

    @patch("tool_batch.execute_tool")
    def test_single_tool_still_works(self, mock_execute):
        mock_execute.return_value = {
            "outgoing_transactions": 3,
            "incoming_transactions": 0,
        }

        args = {
            "bank_id": 3208,
            "account_number": "8000F4580",
        }

        client = Mock()
        client.models.generate_content.side_effect = [
            tool_response(
                ("investigate_account", args)
            ),
            final_response(
                "3 outgoing and 0 incoming"
            ),
        ]

        answer = ask_agent(
            client,
            "Investigate this account",
        )

        self.assertIn("3 outgoing", answer)

        mock_execute.assert_called_once_with(
            "investigate_account",
            args,
        )

        history = (
            client.models.generate_content
            .call_args_list[1]
            .kwargs["contents"]
        )

        self.assertEqual(
            history[2].role,
            "user",
        )

        self.assertEqual(
            history[2].parts[0].function_response.name,
            "investigate_account",
        )

    @patch("tool_batch.execute_tool")
    def test_no_initial_tool_is_rejected(self, mock_execute):
        client = Mock()

        client.models.generate_content.return_value = (
            final_response("No tool used")
        )

        with self.assertRaises(RuntimeError):
            ask_agent(
                client,
                "Investigate transactions",
            )

        mock_execute.assert_not_called()

    @patch("tool_batch.execute_tool")
    def test_multiple_tools_in_one_round(self, mock_execute):
        mock_execute.side_effect = [
            {"transaction_count": 100},
            [{"payment_format": "ACH"}],
        ]

        client = Mock()

        client.models.generate_content.side_effect = [
            tool_response(
                ("inspect_banking_data", {}),
                (
                    "analyze_payment_formats",
                    {"top_n": 5},
                ),
            ),
            final_response(
                "Combined banking analysis"
            ),
        ]

        answer = ask_agent(
            client,
            "Analyze banking data",
        )

        self.assertEqual(
            answer,
            "Combined banking analysis",
        )

        self.assertEqual(
            mock_execute.call_count,
            2,
        )

        history = (
            client.models.generate_content
            .call_args_list[1]
            .kwargs["contents"]
        )

        self.assertEqual(
            len(history[2].parts),
            2,
        )

        self.assertEqual(
            history[2].parts[0].function_response.name,
            "inspect_banking_data",
        )

        self.assertEqual(
            history[2].parts[1].function_response.name,
            "analyze_payment_formats",
        )

    @patch("tool_batch.execute_tool")
    def test_sequential_tool_rounds(self, mock_execute):
        mock_execute.side_effect = [
            {"transaction_count": 100},
            {"outgoing_transactions": 3},
        ]

        client = Mock()

        client.models.generate_content.side_effect = [
            tool_response(
                ("inspect_banking_data", {})
            ),
            tool_response(
                (
                    "investigate_account",
                    {
                        "bank_id": 3208,
                        "account_number": "8000F4580",
                    },
                )
            ),
            final_response(
                "Investigation completed"
            ),
        ]

        answer = ask_agent(
            client,
            "Inspect and investigate",
        )

        self.assertEqual(
            answer,
            "Investigation completed",
        )

        self.assertEqual(
            mock_execute.call_count,
            2,
        )

        self.assertEqual(
            client.models.generate_content.call_count,
            3,
        )

        final_history = (
            client.models.generate_content
            .call_args_list[2]
            .kwargs["contents"]
        )

        self.assertEqual(
            len(final_history),
            5,
        )

    @patch("tool_batch.execute_tool")
    def test_unapproved_tool_rejected(self, mock_execute):
        client = Mock()

        client.models.generate_content.return_value = (
            tool_response(
                ("delete_all_transactions", {})
            )
        )

        with self.assertRaises(ValueError):
            ask_agent(
                client,
                "Delete transactions",
            )

        mock_execute.assert_not_called()

    @patch("tool_batch.execute_tool")
    def test_batch_limit_enforced(self, mock_execute):
        client = Mock()

        client.models.generate_content.return_value = (
            tool_response(
                *[
                    ("inspect_banking_data", {})
                    for _ in range(4)
                ]
            )
        )

        with self.assertRaises(ValueError):
            ask_agent(
                client,
                "Use four tools",
            )

        mock_execute.assert_not_called()

    @patch("tool_batch.execute_tool")
    def test_round_limit_enforced(self, mock_execute):
        mock_execute.return_value = {
            "transaction_count": 100
        }

        client = Mock()

        client.models.generate_content.side_effect = [
            tool_response(
                ("inspect_banking_data", {})
            )
            for _ in range(4)
        ]

        with self.assertRaisesRegex(
            RuntimeError,
            "Tool round limit exceeded",
        ):
            ask_agent(
                client,
                "Keep inspecting",
            )

        self.assertEqual(
            mock_execute.call_count,
            3,
        )

    @patch("tool_batch.execute_tool")
    def test_invalid_arguments_can_be_retried(self, mock_execute):
        """Verify invalid arguments are safely handled and retried."""

        mock_execute.side_effect = [
            ValueError(
                "Sensitive internal error detail"
            ),
            [
                {"payment_format": "ACH"}
            ],
        ]

        client = Mock()

        client.models.generate_content.side_effect = [
            tool_response(
                (
                    "analyze_payment_formats",
                    {"top_n": 0},
                )
            ),

            tool_response(
                (
                    "analyze_payment_formats",
                    {"top_n": 5},
                )
            ),

            final_response(
                "Payment analysis completed"
            ),
        ]

        answer = ask_agent(
            client,
            "Analyze the top 5 payment groups",
        )

        self.assertEqual(
            answer,
            "Payment analysis completed",
        )

        self.assertEqual(
            mock_execute.call_count,
            2,
        )

        self.assertEqual(
            client.models.generate_content.call_count,
            3,
        )
        second_request = (
            client.models.generate_content
            .call_args_list[1]
        )

        history = second_request.kwargs["contents"]

        error_payload = (
            history[2]
            .parts[0]
            .function_response
            .response
        )

        self.assertEqual(
            error_payload["error"]["code"],
            "INVALID_ARGUMENTS",
        )

        self.assertNotIn(
            "Sensitive internal error detail",
            str(error_payload),
        )

        self.assertEqual(
            mock_execute.call_args_list[1].args,
            (
                "analyze_payment_formats",
                {"top_n": 5},
            ),
        )

        third_request = (
            client.models.generate_content
            .call_args_list[2]
        )

        final_history = third_request.kwargs["contents"]

        success_payload = (
            final_history[4]
            .parts[0]
            .function_response
            .response
        )

        self.assertIn(
            "result",
            success_payload,
        )


if __name__ == "__main__":
    unittest.main()
