
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


project_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from api import app, get_overview_data, get_payment_data


class TestInsightForgeAPI(unittest.TestCase):

    def setUp(self):
        get_overview_data.cache_clear()
        self.client = TestClient(app)

    def tearDown(self):
        get_overview_data.cache_clear()

    def test_health(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    @patch("api.execute_tool")
    def test_overview_uses_banking_tool(self, mock_tool):
        mock_tool.return_value = {
            "transaction_count": 5078345,
            "account_count": 518581,
            "laundering_label_count": 5177,
            "payment_currency_count": 15,
        }

        first = self.client.get("/api/overview")
        second = self.client.get("/api/overview")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(
            first.json()["transaction_count"],
            5078345,
        )
        self.assertEqual(first.json(), second.json())

        # The cache avoids repeating the dataset query.
        mock_tool.assert_called_once_with(
            "inspect_banking_data"
        )

    @patch("api.execute_tool")
    def test_missing_dataset_returns_safe_error(self, mock_tool):
        mock_tool.side_effect = FileNotFoundError(
            "/private/internal/path.csv"
        )

        response = self.client.get("/api/overview")

        self.assertEqual(response.status_code, 503)
        self.assertNotIn(
            "/private/internal/path.csv",
            response.text,
        )

    
    @patch("api.execute_tool")
    def test_payment_analysis_endpoint(self, mock_tool):
        mock_tool.return_value = [
            {
                "payment_format": "ACH",
                "currency": "USD",
                "transaction_count": 240028,
                "labeled_count": 1663,
                "labeled_percentage": 0.693,
            }
        ]

        get_payment_data.cache_clear()

        try:
            response = self.client.get("/api/payments")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), 1)
            self.assertEqual(
                response.json()[0]["payment_format"],
                "ACH",
            )

            mock_tool.assert_called_once_with(
                "analyze_payment_formats",
                {"top_n": 10},
            )
        finally:
            get_payment_data.cache_clear()

    
    @patch("api.execute_tool")
    def test_account_investigation_success(self, mock_tool):
        mock_tool.return_value = {
            "bank_id": 3208,
            "account_number": "8000F4580",
            "total_transactions": 3,
            "incoming_transactions": 0,
            "outgoing_transactions": 3,
            "self_transfers": 0,
            "labeled_transactions": 0,
        }

        response = self.client.post(
            "/api/accounts/investigate",
            json={
                "bank_id": 3208,
                "account_number": "8000F4580",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["outgoing_transactions"], 3
        )

        mock_tool.assert_called_once_with(
            "investigate_account",
            {
                "bank_id": 3208,
                "account_number": "8000F4580",
            },
        )

    @patch("api.execute_tool")
    def test_negative_bank_id_rejected(self, mock_tool):
        response = self.client.post(
            "/api/accounts/investigate",
            json={
                "bank_id": -1,
                "account_number": "8000F4580",
            },
        )

        self.assertEqual(response.status_code, 422)
        mock_tool.assert_not_called()

    @patch("api.execute_tool")
    def test_missing_account_dataset(self, mock_tool):
        mock_tool.side_effect = FileNotFoundError(
            "/private/internal/transactions.csv"
        )

        response = self.client.post(
            "/api/accounts/investigate",
            json={
                "bank_id": 3208,
                "account_number": "8000F4580",
            },
        )

        self.assertEqual(response.status_code, 503)
        self.assertNotIn(
            "/private/internal/",
            response.text,
        )


if __name__ == "__main__":
    unittest.main()
