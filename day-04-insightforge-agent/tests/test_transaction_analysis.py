
import sys
import tempfile
import unittest
from pathlib import Path

project_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from tools.transaction_analysis import analyze_payment_formats


class TestTransactionAnalysis(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "transactions.csv"

        self.csv_path.write_text(
            "Payment Format,Payment Currency,Is Laundering\n"
            "ACH,US Dollar,1\n"
            "ACH,US Dollar,0\n"
            "ACH,US Dollar,0\n"
            "ACH,Euro,1\n"
            "ACH,Euro,0\n"
            "Cheque,US Dollar,0\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_grouping_and_percentages(self):
        results = analyze_payment_formats(self.csv_path)

        self.assertEqual(len(results), 3)

        first = results[0]
        self.assertEqual(first["payment_format"], "ACH")
        self.assertEqual(first["currency"], "US Dollar")
        self.assertEqual(first["transaction_count"], 3)
        self.assertEqual(first["labeled_count"], 1)
        self.assertAlmostEqual(
            first["labeled_percentage"], 33.333, places=3
        )

        second = results[1]
        self.assertEqual(second["currency"], "Euro")
        self.assertEqual(second["transaction_count"], 2)
        self.assertEqual(second["labeled_percentage"], 50.0)

    def test_top_n_limit(self):
        results = analyze_payment_formats(
            self.csv_path, top_n=2
        )
        self.assertEqual(len(results), 2)

    def test_zero_labeled_transactions(self):
        results = analyze_payment_formats(self.csv_path)

        cheque = next(
            row for row in results
            if row["payment_format"] == "Cheque"
        )

        self.assertEqual(cheque["labeled_count"], 0)
        self.assertEqual(cheque["labeled_percentage"], 0.0)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            analyze_payment_formats(
                "nonexistent_transactions.csv"
            )

    def test_invalid_top_n(self):
        for invalid_value in [0, 101, -1, "ten", True]:
            with self.subTest(value=invalid_value):
                with self.assertRaises(ValueError):
                    analyze_payment_formats(
                        self.csv_path,
                        top_n=invalid_value,
                    )


if __name__ == "__main__":
    unittest.main()
