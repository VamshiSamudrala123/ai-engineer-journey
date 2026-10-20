
import sys
import tempfile
import unittest
from pathlib import Path

project_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from tools.account_investigation import investigate_account


class TestAccountInvestigation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.csv_path = Path(self.temp_dir.name) / "transactions.csv"

        self.csv_path.write_text(
            "From Bank,Account,To Bank,Account_1,Is Laundering\n"
            "010,ACC-A,020,ACC-B,0\n"
            "020,ACC-C,010,ACC-A,0\n"
            "010,ACC-A,010,ACC-A,1\n"
            "10,ACC-A,099,ACC-D,1\n"
            "099,ACC-E,10,ACC-A,1\n"
            "020,ACC-Z,099,ACC-A,1\n"
            "099,ACC-A,020,ACC-G,1\n",
            encoding="utf-8",
        )

    def test_incoming_outgoing_and_self_transfers(self):
        result = investigate_account(
            self.csv_path, 10, "ACC-A"
        )

        self.assertEqual(result["total_transactions"], 5)
        self.assertEqual(result["outgoing_transactions"], 2)
        self.assertEqual(result["incoming_transactions"], 2)
        self.assertEqual(result["self_transfers"], 1)
        self.assertEqual(result["labeled_transactions"], 3)

        # Every relevant transaction is counted once.
        self.assertEqual(
            result["total_transactions"],
            result["outgoing_transactions"]
            + result["incoming_transactions"]
            + result["self_transfers"],
        )

    def test_same_account_number_at_another_bank(self):
        result = investigate_account(
            self.csv_path, 99, "ACC-A"
        )

        # ACC-A at bank 99 is not ACC-A at bank 10.
        self.assertEqual(result["total_transactions"], 2)
        self.assertEqual(result["outgoing_transactions"], 1)
        self.assertEqual(result["incoming_transactions"], 1)

    def test_leading_zero_bank_codes(self):
        result = investigate_account(
            self.csv_path, 10, "ACC-A"
        )

        # Both 010 and 10 should match bank ID 10.
        self.assertEqual(result["bank_id"], 10)
        self.assertEqual(result["total_transactions"], 5)

    def test_unknown_account(self):
        result = investigate_account(
            self.csv_path, 10, "UNKNOWN"
        )

        self.assertEqual(result["total_transactions"], 0)
        self.assertEqual(result["outgoing_transactions"], 0)
        self.assertEqual(result["incoming_transactions"], 0)
        self.assertEqual(result["self_transfers"], 0)
        self.assertEqual(result["labeled_transactions"], 0)

    def test_missing_file(self):
        missing = Path(self.temp_dir.name) / "missing.csv"

        with self.assertRaises(FileNotFoundError):
            investigate_account(missing, 10, "ACC-A")

    def test_invalid_bank_id(self):
        for invalid in [-1, True, "10", 10.5]:
            with self.subTest(bank_id=invalid):
                with self.assertRaises(ValueError):
                    investigate_account(
                        self.csv_path, invalid, "ACC-A"
                    )

    def test_invalid_account_number(self):
        for invalid in ["", "   ", None, 123]:
            with self.subTest(account_number=invalid):
                with self.assertRaises(ValueError):
                    investigate_account(
                        self.csv_path, 10, invalid
                    )


if __name__ == "__main__":
    unittest.main()
