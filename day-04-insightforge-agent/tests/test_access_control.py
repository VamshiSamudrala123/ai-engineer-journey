"""Isolated tests for production access checks before API integration."""
import base64
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from access_control import require_production_access


class TestProductionAccessControl(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(os.environ, {
            "INSIGHTFORGE_ENV": "production",
            "INSIGHTFORGE_ACCESS_USERNAME": "reviewer",
            "INSIGHTFORGE_ACCESS_PASSWORD": "example-test-password-2026",
        })
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def request(self, path="/api/chat", method="POST", auth=None):
        return SimpleNamespace(
            method=method,
            url=SimpleNamespace(path=path),
            headers={"authorization": auth} if auth else {},
        )

    def basic(self, username="reviewer", password="example-test-password-2026"):
        raw = f"{username}:{password}".encode("utf-8")
        return "Basic " + base64.b64encode(raw).decode("ascii")

    def test_local_development_remains_unrestricted(self):
        with patch.dict(os.environ, {"INSIGHTFORGE_ENV": "development"}):
            self.assertIsNone(require_production_access(self.request()))

    def test_production_without_credentials_fails_closed(self):
        with patch.dict(os.environ, {"INSIGHTFORGE_ACCESS_PASSWORD": ""}):
            denial = require_production_access(self.request())
        self.assertEqual(denial.status_code, 503)

    def test_production_rejects_short_password_configuration(self):
        with patch.dict(os.environ, {"INSIGHTFORGE_ACCESS_PASSWORD": "short"}):
            denial = require_production_access(self.request())
        self.assertEqual(denial.status_code, 503)

    def test_production_rejects_missing_authorization(self):
        denial = require_production_access(self.request())
        self.assertEqual(denial.status_code, 401)
        self.assertIn("Basic", denial.headers["www-authenticate"])

    def test_production_rejects_malformed_basic_authorization(self):
        denial = require_production_access(self.request(auth="Basic ###"))
        self.assertEqual(denial.status_code, 401)

    def test_production_rejects_incorrect_username(self):
        denial = require_production_access(self.request(auth=self.basic(username="other")))
        self.assertEqual(denial.status_code, 401)

    def test_production_rejects_incorrect_password(self):
        denial = require_production_access(self.request(auth=self.basic(password="wrong")))
        self.assertEqual(denial.status_code, 401)

    def test_production_accepts_correct_credentials(self):
        self.assertIsNone(require_production_access(self.request(auth=self.basic())))

    def test_public_health_check_remains_available_without_credentials(self):
        with patch.dict(os.environ, {"INSIGHTFORGE_ACCESS_PASSWORD": ""}):
            self.assertIsNone(require_production_access(
                self.request(path="/api/health", method="GET")
            ))

    def test_docs_are_protected_in_production(self):
        denial = require_production_access(self.request(path="/docs", method="GET"))
        self.assertEqual(denial.status_code, 401)


if __name__ == "__main__":
    unittest.main()
