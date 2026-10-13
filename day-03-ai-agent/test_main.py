import contextlib
import io
import os
import unittest
from unittest.mock import patch

import main


class TerminalTests(unittest.TestCase):
    def test_missing_key_stops_before_sdk_import(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "   "}), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main.main(), 1)
        self.assertIn("Missing GEMINI_API_KEY", out.getvalue())

    def test_confirmation_needs_yes(self):
        task = {"id": "a", "title": "Read"}
        for answer, expected in (("yes", True), (" YES ", True), ("y", False), ("", False), ("no", False)):
            with patch("builtins.input", return_value=answer), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main.confirm_update(task), expected)

    def test_errors_do_not_contain_credentials_or_request_payloads(self):
        for code in (400, 401, 403, 404, 429, 500):
            self.assertTrue(main.api_error_message(code))


if __name__ == "__main__":
    unittest.main()
