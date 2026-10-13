"""Run Streamlit's test harness without sending any Gemini requests."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

try:
    from streamlit.testing.v1 import AppTest
    from google.genai import types as sdk_types
except ImportError:
    AppTest = None
    sdk_types = None


APP = Path(__file__).with_name("web_app.py")


@unittest.skipIf(AppTest is None, "Install requirements.txt for Streamlit checks.")
class WebAppTests(unittest.TestCase):
    def setUp(self):
        # Earlier controller tests replace the SDK. Load the real module here.
        sys.modules.pop("agent", None)

    def make_app(self):
        return AppTest.from_file(str(APP), default_timeout=20)

    def test_no_key_shows_setup_and_disables_chat(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            app = self.make_app().run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(app.chat_input[0].disabled)
            self.assertIn("GEMINI_API_KEY", app.info[0].value)

    def test_chat_and_new_chat_use_the_same_session_tasks(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch("google.genai.Client") as factory:
                client = factory.return_value.__enter__.return_value
                client.models.generate_content.return_value = sdk_types.GenerateContentResponse(candidates=[
                    sdk_types.Candidate(content=sdk_types.Content(role="model", parts=[
                        sdk_types.Part.from_text(text="Start with the tool loop."),
                    ])),
                ])
                app = self.make_app().run()
                app.chat_input[0].set_value("Where should I start?").run()
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(len(app.chat_message), 2)
                self.assertTrue(any("Start with the tool loop." in item.value for item in app.markdown))
                factory.return_value.__exit__.assert_called_once()
                app.sidebar.button[0].click().run()
                self.assertEqual(len(app.chat_message), 0)
                self.assertEqual(len(app.session_state["task_store"].list_pending_tasks()["tasks"]), 4)

    def test_confirm_and_cancel_buttons_control_task_updates(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            app = self.make_app().run()
            agent = app.session_state["agent"]
            agent.execute_tool("mark_task_done", {"task_id": "tool-loop"})
            app.run()
            self.assertTrue(app.chat_input[0].disabled)
            next(button for button in app.button if button.label == "Cancel").click().run()
            self.assertFalse(app.session_state["task_store"].all_tasks()[0]["done"])
            agent.execute_tool("mark_task_done", {"task_id": "tool-loop"})
            app.run()
            next(button for button in app.button if button.label == "Confirm completion").click().run()
            self.assertTrue(app.session_state["task_store"].all_tasks()[0]["done"])
            self.assertFalse(app.chat_input[0].disabled)
            app.sidebar.button[1].click().run()
            self.assertFalse(app.session_state["task_store"].all_tasks()[0]["done"])
            self.assertEqual(len(app.exception), 0)

    def test_api_failure_is_sanitized(self):
        from google.genai import errors
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch("google.genai.Client") as factory:
                client = factory.return_value.__enter__.return_value
                client.models.generate_content.side_effect = errors.ClientError(
                    403, {"error": {"message": "private request details", "status": "PERMISSION_DENIED"}},
                )
                app = self.make_app().run()
                app.chat_input[0].set_value("Hello").run()
                self.assertEqual(len(app.exception), 0)
                self.assertTrue(any("permissions" in item.value for item in app.markdown))
                self.assertFalse(any("private request details" in item.value for item in app.markdown))


if __name__ == "__main__":
    unittest.main()
