"""Production dashboard routing and access tests without real CSV or Gemini."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api import app


class TestProductionDashboardServing(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dist = Path(self.temp.name)
        (self.dist / "assets").mkdir()
        (self.dist / "index.html").write_text(
            "<!doctype html><html><body>InsightForge dashboard</body></html>",
            encoding="utf-8",
        )
        (self.dist / "assets" / "app.123.js").write_text(
            "console.log('InsightForge')", encoding="utf-8"
        )
        self.patch_dist = patch("api.DASHBOARD_DIST", self.dist)
        self.patch_dist.start()
        self.addCleanup(self.patch_dist.stop)
        self.client = TestClient(app)

    def test_local_home_serves_react(self):
        with patch.dict(os.environ, {"INSIGHTFORGE_ENV": "development"}):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("InsightForge dashboard", response.text)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_serves_vite_asset(self):
        with patch.dict(os.environ, {"INSIGHTFORGE_ENV": "development"}):
            response = self.client.get("/assets/app.123.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn("console.log", response.text)
        self.assertIn("private", response.headers["cache-control"])

    def test_react_deep_link_refresh(self):
        with patch.dict(os.environ, {"INSIGHTFORGE_ENV": "development"}):
            response = self.client.get("/account-investigation")
        self.assertEqual(response.status_code, 200)
        self.assertIn("InsightForge dashboard", response.text)

    def test_unknown_api_route_does_not_return_html(self):
        with patch.dict(os.environ, {"INSIGHTFORGE_ENV": "development"}):
            response = self.client.get("/api/not-a-route")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("InsightForge dashboard", response.text)

    def test_missing_asset_returns_404(self):
        with patch.dict(os.environ, {"INSIGHTFORGE_ENV": "development"}):
            response = self.client.get("/assets/missing.js")
        self.assertEqual(response.status_code, 404)

    def test_missing_build_returns_helpful_503(self):
        with (
            patch.dict(os.environ, {"INSIGHTFORGE_ENV": "development"}),
            patch("api.DASHBOARD_DIST", self.dist / "not-built"),
        ):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 503)

    def test_production_blocks_anonymous_home(self):
        with patch.dict(os.environ, {
            "INSIGHTFORGE_ENV": "production",
            "INSIGHTFORGE_ACCESS_USERNAME": "reviewer",
            "INSIGHTFORGE_ACCESS_PASSWORD": "long-test-password-12345",
        }):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 401)

    def test_production_blocks_anonymous_javascript(self):
        with patch.dict(os.environ, {
            "INSIGHTFORGE_ENV": "production",
            "INSIGHTFORGE_ACCESS_USERNAME": "reviewer",
            "INSIGHTFORGE_ACCESS_PASSWORD": "long-test-password-12345",
        }):
            response = self.client.get("/assets/app.123.js")
        self.assertEqual(response.status_code, 401)

    def test_production_allows_authorized_home(self):
        with patch.dict(os.environ, {
            "INSIGHTFORGE_ENV": "production",
            "INSIGHTFORGE_ACCESS_USERNAME": "reviewer",
            "INSIGHTFORGE_ACCESS_PASSWORD": "long-test-password-12345",
        }):
            response = self.client.get(
                "/", auth=("reviewer", "long-test-password-12345")
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("InsightForge dashboard", response.text)


if __name__ == "__main__":
    unittest.main()
