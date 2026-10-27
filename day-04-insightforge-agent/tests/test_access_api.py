"""Integration tests for private FastAPI access, without network/Gemini calls."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api import app


class TestPrivateDemoAccessAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def production(self, **overrides):
        values = {
            "INSIGHTFORGE_ENV": "production",
            "INSIGHTFORGE_ACCESS_USERNAME": "reviewer",
            "INSIGHTFORGE_ACCESS_PASSWORD": "sample-test-password-2026",
            "INSIGHTFORGE_ENABLE_CHAT": "false",
        }
        values.update(overrides)
        return patch.dict(os.environ, values)

    def test_development_keeps_api_usable_without_login(self):
        with (
            patch.dict(os.environ, {"INSIGHTFORGE_ENV": "development"}),
            patch("api.get_overview_data", return_value={"status": "ready"}),
        ):
            response = self.client.get("/api/overview")
        self.assertEqual(response.status_code, 200)

    def test_production_without_config_fails_closed(self):
        with self.production(INSIGHTFORGE_ACCESS_PASSWORD=""):
            response = self.client.get("/docs")
        self.assertEqual(response.status_code, 503)

    def test_production_requires_authentication(self):
        with self.production():
            response = self.client.get("/api/overview")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Basic", response.headers["www-authenticate"])
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_wrong_password_rejected(self):
        with self.production():
            response = self.client.get("/docs", auth=("reviewer", "wrong"))
        self.assertEqual(response.status_code, 401)

    def test_correct_password_allows_approved_route(self):
        with (
            self.production(),
            patch("api.get_overview_data", return_value={"status": "ready"}),
        ):
            response = self.client.get(
                "/api/overview", auth=("reviewer", "sample-test-password-2026")
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})

    def test_health_remains_public_even_without_credentials(self):
        with self.production(INSIGHTFORGE_ACCESS_PASSWORD=""):
            response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

    def test_openapi_schema_is_private(self):
        with self.production():
            response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 401)

    def test_unauthorized_pdf_request_never_runs_generator(self):
        with (
            self.production(),
            patch("api.generate_account_report") as generator,
        ):
            response = self.client.post(
                "/api/reports/account",
                json={"bank_id": 3208, "account_number": "8000F4580"},
            )
        self.assertEqual(response.status_code, 401)
        generator.assert_not_called()


if __name__ == "__main__":
    unittest.main()
