"""Offline behavior tests. No API key, network requests, or quota required."""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location("chatbot", Path(__file__).with_name("main.py"))
chatbot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chatbot)


class FakeAPIError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__("Simulated error with private request details")


class FakeTransportError(Exception):
    pass


class FakeTimeout(FakeTransportError):
    pass


class ChatbotTests(unittest.TestCase):
    def setUp(self):
        # Simulate only the SDK boundary. All application code runs normally.
        self.client = Mock()
        self.client.__enter__ = Mock(return_value=self.client)
        self.client.__exit__ = Mock(return_value=False)
        self.client_factory = Mock(return_value=self.client)
        genai = types.ModuleType("google.genai")
        genai.Client = self.client_factory
        genai.errors = types.SimpleNamespace(APIError=FakeAPIError)
        genai.types = types.SimpleNamespace(
            HttpOptions=lambda **kwargs: types.SimpleNamespace(**kwargs),
            GenerateContentConfig=lambda **kwargs: types.SimpleNamespace(**kwargs),
        )
        google = types.ModuleType("google")
        google.genai = genai
        httpx = types.ModuleType("httpx")
        httpx.TransportError = FakeTransportError
        httpx.TimeoutException = FakeTimeout
        self.modules = patch.dict(sys.modules, {
            "google": google,
            "google.genai": genai,
            "httpx": httpx,
        })
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def run_with_input(self, chat, inputs):
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), contextlib.redirect_stdout(output):
            result = chatbot.run_chat(chat)
        return result, output.getvalue()

    def test_missing_key_stops_before_creating_client(self):
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(chatbot.main(), 1)
        self.assertIn("Missing GEMINI_API_KEY", out.getvalue())
        self.client_factory.assert_not_called()

    def test_whitespace_key_is_rejected(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "   "}, clear=True):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(chatbot.main(), 1)
        self.client_factory.assert_not_called()

    def test_client_configuration_and_cleanup(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-credential"}, clear=True):
            with patch("builtins.input", return_value="exit"), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(chatbot.main(), 0)
        self.assertNotIn("test-credential", out.getvalue())
        arguments = self.client_factory.call_args.kwargs
        self.assertEqual(arguments["api_key"], "test-credential")
        self.assertFalse(arguments["vertexai"])
        self.assertEqual(arguments["http_options"].timeout, 30_000)
        self.assertEqual(self.client.chats.create.call_args.kwargs["model"], chatbot.DEFAULT_MODEL)
        self.client.__exit__.assert_called_once()

    def test_custom_model_is_used(self):
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test-credential", "GEMINI_MODEL": " custom-model "
        }, clear=True), patch("builtins.input", return_value="quit"):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(chatbot.main(), 0)
        self.assertEqual(self.client.chats.create.call_args.kwargs["model"], "custom-model")

    def test_blank_messages_make_no_api_calls(self):
        chat = Mock()
        result, output = self.run_with_input(chat, ["", "   ", "exit"])
        self.assertEqual(result, 0)
        self.assertEqual(output.count("Please enter a message."), 2)
        chat.send_message.assert_not_called()

    def test_exit_commands_are_case_insensitive(self):
        for command in ["exit", "QUIT", " Exit "]:
            with self.subTest(command=command):
                chat = Mock()
                result, output = self.run_with_input(chat, [command])
                self.assertEqual(result, 0)
                self.assertIn("Goodbye!", output)
                chat.send_message.assert_not_called()

    def test_messages_reuse_one_chat_and_display_responses(self):
        chat = Mock()
        chat.send_message.side_effect = [
            types.SimpleNamespace(text="Nice choice!"),
            types.SimpleNamespace(text="Python."),
        ]
        result, output = self.run_with_input(chat, [" I like Python. ", "What do I like?", "quit"])
        self.assertEqual(result, 0)
        self.assertEqual([call.args[0] for call in chat.send_message.call_args_list],
                         ["I like Python.", "What do I like?"])
        self.assertIn("AI: Python.", output)

    def test_no_text_response_keeps_loop_usable(self):
        for text in [None, "", "   "]:
            with self.subTest(text=text):
                chat = Mock()
                chat.send_message.return_value = types.SimpleNamespace(text=text)
                result, output = self.run_with_input(chat, ["Hello", "exit"])
                self.assertEqual(result, 0)
                self.assertIn("returned no text", output)

    def test_configuration_errors_stop_without_raw_details(self):
        for code in [400, 401, 403, 404]:
            with self.subTest(code=code):
                chat = Mock()
                chat.send_message.side_effect = FakeAPIError(code)
                result, output = self.run_with_input(chat, ["Hello"])
                self.assertEqual(result, 1)
                self.assertIn(f"API error ({code})", output)
                self.assertNotIn("private request details", output)

    def test_quota_and_server_errors_allow_next_message(self):
        for code in [429, 500, 503]:
            with self.subTest(code=code):
                chat = Mock()
                chat.send_message.side_effect = [FakeAPIError(code), types.SimpleNamespace(text="Recovered")]
                result, output = self.run_with_input(chat, ["Hello", "Try again", "exit"])
                self.assertEqual(result, 0)
                self.assertIn("AI: Recovered", output)

    def test_network_errors_allow_retry(self):
        for error, expected in [(FakeTimeout(), "timed out"), (FakeTransportError(), "Connection failed")]:
            with self.subTest(expected=expected):
                chat = Mock()
                chat.send_message.side_effect = [error, types.SimpleNamespace(text="Recovered")]
                result, output = self.run_with_input(chat, ["Hello", "Try again", "exit"])
                self.assertEqual(result, 0)
                self.assertIn(expected, output)
                self.assertIn("AI: Recovered", output)

    def test_eof_and_interrupt_exit_cleanly(self):
        for exception in [EOFError(), KeyboardInterrupt()]:
            with self.subTest(exception=type(exception).__name__):
                result, output = self.run_with_input(Mock(), [exception])
                self.assertEqual(result, 0)
                self.assertIn("Goodbye!", output)

    def test_client_closed_after_fatal_api_error(self):
        self.client.chats.create.return_value.send_message.side_effect = FakeAPIError(403)
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-credential"}, clear=True):
            with patch("builtins.input", return_value="Hello"), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(chatbot.main(), 1)
        self.client.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
