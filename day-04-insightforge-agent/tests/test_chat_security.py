import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chat_security import ChatRateLimiter, protect_chat_request


class TestChatSecurity(unittest.TestCase):
    def test_allows_requests_within_limit(self):
        limiter = ChatRateLimiter(per_client=2, global_limit=3)
        limiter.check("first", now=100)
        limiter.check("first", now=101)

    def test_rejects_excess_client_requests(self):
        limiter = ChatRateLimiter(per_client=1, global_limit=10)
        limiter.check("first", now=100)
        with self.assertRaises(HTTPException) as caught:
            limiter.check("first", now=101)
        self.assertEqual(caught.exception.status_code, 429)
        self.assertIn("Retry-After", caught.exception.headers)

    def test_global_limit_applies_across_clients(self):
        limiter = ChatRateLimiter(per_client=2, global_limit=2)
        limiter.check("first", now=100)
        limiter.check("second", now=101)
        with self.assertRaises(HTTPException) as caught:
            limiter.check("third", now=102)
        self.assertEqual(caught.exception.status_code, 429)

    def test_requests_allowed_after_window_expires(self):
        limiter = ChatRateLimiter(per_client=1, global_limit=1, window_seconds=60)
        limiter.check("first", now=100)
        limiter.check("first", now=160)

    def test_production_chat_disabled_by_default(self):
        request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
        with patch.dict(os.environ, {
            "INSIGHTFORGE_ENV": "production",
            "INSIGHTFORGE_ENABLE_CHAT": "false",
        }):
            with self.assertRaises(HTTPException) as caught:
                protect_chat_request(request)
        self.assertEqual(caught.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
