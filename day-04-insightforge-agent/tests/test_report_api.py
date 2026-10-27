"""Regression tests for the PDF report download endpoint (no private data)."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

project_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from api import app


class TestAccountReportAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.request = {
            "bank_id": 3208,
            "account_number": "8000F4580",
        }

    @patch("api.generate_account_report")
    def test_download_pdf_and_headers(self, mock_generate):
        fake_pdf = b"%PDF-1.4\nsynthetic test pdf\n%%EOF"
        mock_generate.return_value = fake_pdf

        response = self.client.post("/api/reports/account", json=self.request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertIn("attachment;", response.headers["content-disposition"])
        self.assertIn(".pdf", response.headers["content-disposition"])
        self.assertEqual(response.content, fake_pdf)
        mock_generate.assert_called_once_with(
            bank_id=3208, account_number="8000F4580"
        )

    @patch("api.generate_account_report")
    def test_negative_bank_id_is_rejected(self, mock_generate):
        response = self.client.post(
            "/api/reports/account",
            json={"bank_id": -1, "account_number": "ACC-1"},
        )
        self.assertEqual(response.status_code, 422)
        mock_generate.assert_not_called()

    @patch("api.generate_account_report")
    def test_blank_account_is_rejected(self, mock_generate):
        response = self.client.post(
            "/api/reports/account",
            json={"bank_id": 3208, "account_number": "   "},
        )
        self.assertEqual(response.status_code, 422)
        mock_generate.assert_not_called()

    @patch("api.generate_account_report")
    def test_account_number_is_trimmed(self, mock_generate):
        mock_generate.return_value = b"%PDF-1.4\n%%EOF"
        response = self.client.post(
            "/api/reports/account",
            json={"bank_id": 3208, "account_number": "  ACC-1  "},
        )
        self.assertEqual(response.status_code, 200)
        mock_generate.assert_called_once_with(
            bank_id=3208, account_number="ACC-1"
        )

    @patch("api.generate_account_report")
    def test_missing_dataset_returns_503(self, mock_generate):
        mock_generate.side_effect = FileNotFoundError("/private/data.csv")
        response = self.client.post("/api/reports/account", json=self.request)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("/private/data.csv", response.text)

    @patch("api.generate_account_report")
    def test_invalid_report_data_returns_safe_500(self, mock_generate):
        mock_generate.side_effect = ValueError("private internal values")
        response = self.client.post("/api/reports/account", json=self.request)
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private internal values", response.text)

    @patch("api.generate_account_report")
    def test_non_pdf_bytes_are_rejected(self, mock_generate):
        mock_generate.return_value = b"This is not a PDF"
        response = self.client.post("/api/reports/account", json=self.request)
        self.assertEqual(response.status_code, 500)

    @patch("api.generate_account_report")
    def test_unexpected_error_returns_safe_500(self, mock_generate):
        mock_generate.side_effect = RuntimeError("secret rendering error")
        response = self.client.post("/api/reports/account", json=self.request)
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret rendering error", response.text)


if __name__ == "__main__":
    unittest.main()
