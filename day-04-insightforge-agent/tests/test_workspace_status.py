"""Coverage for the UI's safe data-source and AI readiness endpoint."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api import app


class WorkspaceStatusTests(unittest.TestCase):
    def test_demo_source_is_disclosed_without_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            transactions = Path(directory) / "HI-Small_Trans.csv"
            accounts = Path(directory) / "HI-Small_accounts.csv"
            transactions.write_text("data", encoding="utf-8")
            accounts.write_text("data", encoding="utf-8")
            with (
                patch.dict(os.environ, {
                    "INSIGHTFORGE_ENV": "development",
                    "INSIGHTFORGE_DEMO_DATA": "true",
                    "INSIGHTFORGE_ENABLE_CHAT": "false",
                    "GEMINI_API_KEY": "private-test-key",
                }),
                patch("api.TRANSACTIONS", transactions),
                patch("api.ACCOUNTS", accounts),
            ):
                response = TestClient(app).get("/api/workspace")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["dataset_type"], "generated_example")
            self.assertTrue(response.json()["dataset_ready"])
            self.assertTrue(response.json()["ai_chat_ready"])
            self.assertNotIn("private-test-key", response.text)

    def test_missing_source_and_disabled_production_ai(self):
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.dict(os.environ, {
                    "INSIGHTFORGE_ENV": "production",
                    "INSIGHTFORGE_DEMO_DATA": "false",
                    "INSIGHTFORGE_ENABLE_CHAT": "false",
                    "GEMINI_API_KEY": "secret",
                    "INSIGHTFORGE_ACCESS_USERNAME": "reviewer",
                    "INSIGHTFORGE_ACCESS_PASSWORD": "long-test-password-12345",
                }),
                patch("api.TRANSACTIONS", Path(directory) / "missing1.csv"),
                patch("api.ACCOUNTS", Path(directory) / "missing2.csv"),
            ):
                response = TestClient(app).get("/api/workspace", auth=("reviewer", "long-test-password-12345"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["dataset_type"], "unavailable")
            self.assertFalse(response.json()["ai_chat_ready"])
            self.assertFalse(response.json()["dataset_ready"])


if __name__ == "__main__":
    unittest.main()
