"""Check real SDK request shapes with mocked network responses."""

import sys
import unittest
from unittest.mock import Mock

try:
    from google.genai import types as sdk_types
except ImportError:
    sdk_types = None


@unittest.skipIf(sdk_types is None, "Install requirements.txt for SDK checks.")
class SdkTests(unittest.TestCase):
    def test_real_sdk_keeps_call_id_signature_and_result(self):
        sys.modules.pop("agent", None)
        from agent import StudyAgent
        client = Mock()
        content = sdk_types.Content(role="model", parts=[sdk_types.Part(
            function_call=sdk_types.FunctionCall(
                name="calculate_study_time", args={"minutes_per_day": 90, "days": 5}, id="call-1",
            ), thought_signature=b"signature",
        )])
        client.models.generate_content.side_effect = [
            sdk_types.GenerateContentResponse(candidates=[sdk_types.Candidate(content=content)]),
            sdk_types.GenerateContentResponse(candidates=[sdk_types.Candidate(content=sdk_types.Content(
                role="model", parts=[sdk_types.Part.from_text(text="7.5 hours.")],
            ))]),
        ]
        agent = StudyAgent(client, "test-model", version=4)
        self.assertEqual(agent.ask("90 minutes for 5 days?"), "7.5 hours.")
        contents = client.models.generate_content.call_args.kwargs["contents"]
        self.assertIs(contents[1], content)
        self.assertEqual(contents[1].parts[0].thought_signature, b"signature")
        self.assertEqual(contents[2].parts[0].function_response.id, "call-1")
        self.assertEqual(contents[2].parts[0].function_response.response["result"]["total_hours"], 7.5)
        self.assertTrue(agent.config.automatic_function_calling.disable)
        self.assertIn("mark_task_done", agent.config.model_dump_json())


if __name__ == "__main__":
    unittest.main()
