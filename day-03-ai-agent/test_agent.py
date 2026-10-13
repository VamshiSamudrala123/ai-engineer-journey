"""Exercise the agent loop with scripted model responses, without API calls."""

import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class FakePart:
    def __init__(self, text=None, function_call=None, function_response=None,
                 thought=False, thought_signature=None):
        self.text = text
        self.function_call = function_call
        self.function_response = function_response
        self.thought = thought
        self.thought_signature = thought_signature

    @classmethod
    def from_text(cls, text):
        return cls(text=text)


def reply(*parts):
    content = types.SimpleNamespace(role="model", parts=list(parts))
    return types.SimpleNamespace(candidates=[types.SimpleNamespace(content=content)])


def tool_call(name="calculate_study_time", args=None, call_id="call-1"):
    return FakePart(function_call=types.SimpleNamespace(
        name=name, args=args if args is not None else {"minutes_per_day": 90, "days": 5},
        id=call_id,
    ), thought_signature=b"preserve-this")


class AgentTests(unittest.TestCase):
    def setUp(self):
        # Only the SDK boundary is replaced. Tools and the controller run normally.
        fake_types = types.SimpleNamespace(
            Part=FakePart, Content=lambda **kw: types.SimpleNamespace(**kw),
            FunctionResponse=lambda **kw: types.SimpleNamespace(**kw),
            FunctionDeclaration=lambda **kw: types.SimpleNamespace(**kw),
            Tool=lambda **kw: types.SimpleNamespace(**kw),
            GenerateContentConfig=lambda **kw: types.SimpleNamespace(**kw),
            AutomaticFunctionCallingConfig=lambda **kw: types.SimpleNamespace(**kw),
        )
        google = types.ModuleType("google")
        genai = types.ModuleType("google.genai")
        genai.types = fake_types
        google.genai = genai
        self.modules = patch.dict(sys.modules, {"google": google, "google.genai": genai})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        sys.modules.pop("agent", None)
        self.module = importlib.import_module("agent")
        self.addCleanup(sys.modules.pop, "agent", None)
        self.client = Mock()
        self.agent = self.module.StudyAgent(self.client, "test-model")

    def test_calculation_result_returns_to_model(self):
        first = reply(tool_call())
        self.client.models.generate_content.side_effect = [first, reply(FakePart(text="7.5 hours."))]
        self.assertEqual(self.agent.ask("90 minutes for 5 days?"), "7.5 hours.")
        contents = self.client.models.generate_content.call_args.kwargs["contents"]
        self.assertIs(contents[1], first.candidates[0].content)
        result = contents[2].parts[0].function_response
        self.assertEqual(result.id, "call-1")
        self.assertEqual(result.response["result"]["total_minutes"], 450)
        self.assertTrue(self.agent.config.automatic_function_calling.disable)

    def test_plain_answer_needs_no_tool(self):
        self.client.models.generate_content.return_value = reply(FakePart(text="Start with one small task."))
        self.assertEqual(self.agent.ask("How can I focus?"), "Start with one small task.")
        self.assertEqual(self.agent.trace, [])

    def test_parallel_calls_keep_their_ids(self):
        self.client.models.generate_content.side_effect = [
            reply(tool_call(call_id="one"), tool_call(args={"minutes_per_day": 60, "days": 2}, call_id="two")),
            reply(FakePart(text="Done.")),
        ]
        self.agent.ask("Compare two study schedules.")
        parts = self.client.models.generate_content.call_args.kwargs["contents"][2].parts
        self.assertEqual([part.function_response.id for part in parts], ["one", "two"])

    def test_unknown_tools_and_bad_arguments_are_rejected(self):
        for name, args in (("run_shell", {"command": "echo hello"}),
                           ("calculate_study_time", {"minutes_per_day": True, "days": 5}),
                           ("calculate_study_time", {"minutes_per_day": 90, "days": 5, "extra": 1}),
                           ("calculate_study_time", None)):
            with self.subTest(name=name, args=args):
                self.assertIn("error", self.agent.execute_tool(name, args))

    def test_repeated_tool_calls_stop(self):
        self.agent.max_rounds = 2
        self.client.models.generate_content.return_value = reply(tool_call())
        with self.assertRaisesRegex(self.module.AgentError, "limit"):
            self.agent.ask("Keep calculating.")
        self.assertEqual(len(self.agent.trace), 2)
        self.assertEqual(self.agent.turns, [])

    def test_oversized_batch_executes_nothing(self):
        self.client.models.generate_content.return_value = reply(*[tool_call() for _ in range(9)])
        with self.assertRaises(self.module.AgentError):
            self.agent.ask("Many calculations.")
        self.assertEqual(self.agent.trace, [])

    def test_blank_and_long_prompts_never_call_model(self):
        for question in ("", "  ", "x" * 4001):
            with self.assertRaises(self.module.AgentError):
                self.agent.ask(question)
        self.client.models.generate_content.assert_not_called()

    def test_missing_and_empty_answers_are_explained(self):
        for response in (types.SimpleNamespace(candidates=[]), reply(FakePart(text=""))):
            self.client.models.generate_content.return_value = response
            with self.assertRaises(self.module.AgentError):
                self.agent.ask("Hello")

    def test_clear_resets_history_and_trace(self):
        self.client.models.generate_content.return_value = reply(FakePart(text="Hello"))
        self.agent.ask("Hello")
        self.agent.clear()
        self.assertEqual(self.agent.turns, [])
        self.assertEqual(self.agent.trace, [])

    def test_v3_combines_multiple_tools(self):
        self.agent = self.module.StudyAgent(self.client, "test-model", version=3)
        self.client.models.generate_content.side_effect = [
            reply(tool_call(), tool_call("list_pending_tasks", {}, "tasks")),
            reply(tool_call("build_study_plan", {"minutes_per_day": 90, "days": 5}, "plan")),
            reply(FakePart(text="Here is your study plan.")),
        ]
        self.assertEqual(self.agent.ask("Plan my week."), "Here is your study plan.")
        self.assertEqual([entry["tool"] for entry in self.agent.trace], [
            "calculate_study_time", "list_pending_tasks", "build_study_plan",
        ])
        self.assertEqual(len(self.agent.trace[-1]["result"]["sessions"]), 5)

    def test_v2_cannot_access_task_tools(self):
        self.assertIn("error", self.agent.execute_tool("list_pending_tasks", {}))


if __name__ == "__main__":
    unittest.main()
