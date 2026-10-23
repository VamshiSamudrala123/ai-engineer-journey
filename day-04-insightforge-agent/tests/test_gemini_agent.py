
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from google.genai import types

# Allow imports from the Project 04 folder.
project_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from gemini_agent import ask_agent


class TestGeminiAgent(unittest.TestCase):

    @patch("gemini_agent.execute_tool")
    def test_gemini_tool_call_and_final_answer(self, mock_tool):
        # Simulate a real banking tool result.
        mock_tool.return_value = {
            "total_transactions": 3,
            "outgoing_transactions": 3,
            "incoming_transactions": 0,
            "self_transfers": 0,
            "labeled_transactions": 0,
        }

        args = {
            "bank_id": 3208,
            "account_number": "8000F4580",
        }

        # Simulate Gemini requesting an approved tool.
        model_content = types.Content(
            role="model",
            parts=[
                types.Part(
                    function_call=types.FunctionCall(
                        name="investigate_account",
                        args=args,
                    )
                )
            ],
        )

        first_response = SimpleNamespace(
            function_calls=[
                SimpleNamespace(
                    name="investigate_account",
                    args=args,
                )
            ],
            candidates=[
                SimpleNamespace(content=model_content)
            ],
        )

        final_response = SimpleNamespace(
            text="The account has 3 outgoing transactions."
        )

        # No actual Gemini API request is made.
        client = Mock()
        client.models.generate_content.side_effect = [
            first_response,
            final_response,
        ]

        answer = ask_agent(
            client,
            "Investigate account 8000F4580 at bank 3208",
        )

        self.assertIn("3 outgoing", answer)

        mock_tool.assert_called_once_with(
            "investigate_account",
            args,
        )

        # First model call selects a tool.
        # Second model call generates the final answer.
        self.assertEqual(
            client.models.generate_content.call_count,
            2,
        )

        # Verify the banking result was returned to Gemini.
        second_request = (
            client.models.generate_content.call_args_list[1]
        )
        history = second_request.kwargs["contents"]

        self.assertEqual(history[-1].role, "user")
        self.assertEqual(
            history[-1].parts[0].function_response.name,
            "investigate_account",
        )

    @patch("gemini_agent.execute_tool")
    def test_no_function_call_is_rejected(self, mock_tool):
        client = Mock()

        client.models.generate_content.return_value = (
            SimpleNamespace(function_calls=[])
        )

        with self.assertRaises(RuntimeError):
            ask_agent(client, "Investigate transactions")

        mock_tool.assert_not_called()

    @patch("gemini_agent.execute_tool")
    def test_multiple_calls_rejected_in_v2(self, mock_tool):
        client = Mock()

        client.models.generate_content.return_value = (
            SimpleNamespace(
                function_calls=[
                    SimpleNamespace(name="inspect_banking_data"),
                    SimpleNamespace(name="analyze_payment_formats"),
                ]
            )
        )

        with self.assertRaises(RuntimeError):
            ask_agent(client, "Analyze multiple banking patterns")

        mock_tool.assert_not_called()


if __name__ == "__main__":
    unittest.main()
