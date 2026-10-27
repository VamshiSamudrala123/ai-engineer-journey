"""Exercise FastAPI chat protection without calling the real Gemini API."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from api import app
from chat_security import ChatRateLimiter


class TestChatEndpointSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Keep test cases independent of the production process-wide limiter.
        limiter_patch = patch(
            "chat_security.limiter",
            ChatRateLimiter(per_client=2, global_limit=3),
        )
        limiter_patch.start()
        self.addCleanup(limiter_patch.stop)

    def test_chat_returns_429_and_retry_after_without_calling_gemini(self):
        with (
            patch.dict(os.environ, {
                "INSIGHTFORGE_ENV": "development",
                "GEMINI_API_KEY": "test-key",
            }),
            patch("api.genai.Client"),
            patch("api.ask_agent", return_value="Verified answer") as agent,
        ):
            for _ in range(2):
                response = self.client.post(
                    "/api/chat", json={"question": "Summarize the dataset"}
                )
                self.assertEqual(response.status_code, 200)

            response = self.client.post(
                "/api/chat", json={"question": "One more question"}
            )
            self.assertEqual(response.status_code, 429)
            self.assertIn("retry-after", response.headers)
            self.assertEqual(agent.call_count, 2)

    def test_production_chat_disabled_by_default(self):
        with (
            patch.dict(os.environ, {
                "INSIGHTFORGE_ENV": "production",
                "INSIGHTFORGE_ENABLE_CHAT": "false",
                "GEMINI_API_KEY": "test-key",
            }),
            patch("api.require_production_access", return_value=None),
            patch("api.genai.Client") as gemini,
        ):
            response = self.client.post(
                "/api/chat", json={"question": "Analyze transactions"}
            )
            self.assertEqual(response.status_code, 503)
            gemini.assert_not_called()

    def test_production_chat_requires_explicit_opt_in(self):
        with (
            patch.dict(os.environ, {
                "INSIGHTFORGE_ENV": "production",
                "INSIGHTFORGE_ENABLE_CHAT": "true",
                "GEMINI_API_KEY": "test-key",
            }),
            patch("api.require_production_access", return_value=None),
            patch("api.genai.Client"),
            patch("api.ask_agent", return_value="Verified answer"),
        ):
            response = self.client.post(
                "/api/chat", json={"question": "Analyze transactions"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["answer"], "Verified answer")

    def test_health_remains_accessible_in_production(self):
        with patch.dict(os.environ, {
            "INSIGHTFORGE_ENV": "production",
            "INSIGHTFORGE_ENABLE_CHAT": "false",
        }):
            response = self.client.get("/api/health")
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
