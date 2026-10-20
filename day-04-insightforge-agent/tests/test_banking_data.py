
import sys
import tempfile
import unittest
from pathlib import Path

# Make the project folder available for imports.
project_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from tools.banking_data import inspect_banking_data


class TestBankingData(unittest.TestCase):

    def setUp(self):
        # Create temporary files for each test.
        self.temp_dir = tempfile.TemporaryDirectory()
        folder = Path(self.temp_dir.name)

        self.transactions = folder / "transactions.csv"
        self.accounts = folder / "accounts.csv"

        self.transactions.write_text(
            "Timestamp,From Bank,Payment Currency,Is Laundering\n"
            "2022-09-01 10:00:00,BankA,USD,0\n"
            "2022-09-02 11:00:00,BankB,EUR,1\n"
            "2022-09-03 12:00:00,BankA,USD,0\n",
            encoding="utf-8",
        )

        self.accounts.write_text(
            "Bank Name,Account Number\n"
            "BankA,ACC001\n"
            "BankB,ACC002\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_correct_statistics(self):
        result = inspect_banking_data(
            self.transactions,
            self.accounts,
        )

        self.assertEqual(result["transaction_count"], 3)
        self.assertEqual(result["account_count"], 2)
        self.assertEqual(
            result["distinct_sending_bank_values"], 2
        )
        self.assertEqual(result["payment_currency_count"], 2)
        self.assertEqual(result["laundering_label_count"], 1)
        self.assertEqual(
            result["first_transaction"],
            "2022-09-01T10:00:00",
        )
        self.assertEqual(
            result["last_transaction"],
            "2022-09-03T12:00:00",
        )

    def test_zero_laundering_labels(self):
        self.transactions.write_text(
            "Timestamp,From Bank,Payment Currency,Is Laundering\n"
            "2022-09-01 10:00:00,BankA,USD,0\n",
            encoding="utf-8",
        )

        result = inspect_banking_data(
            self.transactions,
            self.accounts,
        )

        self.assertEqual(result["laundering_label_count"], 0)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            inspect_banking_data(
                "missing_transactions.csv",
                self.accounts,
            )


if __name__ == "__main__":
    unittest.main()
