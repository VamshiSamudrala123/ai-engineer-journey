"""Tests for the opt-in fictional demo dataset generator."""
import csv
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT_DIR = Path(__file__).resolve().parents[1]
GENERATOR = PROJECT_DIR / "generate_demo_data.py"


class DemoDatasetTests(unittest.TestCase):
    def test_demo_data_has_expected_columns_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, INSIGHTFORGE_DATA_DIR=directory)
            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, str(GENERATOR)],
                    env=env, capture_output=True, text=True, check=True
                )
                self.assertEqual(result.returncode, 0)
            output_dir = Path(directory)
            with (output_dir / "HI-Small_Trans.csv").open(newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
            with (output_dir / "HI-Small_accounts.csv").open(newline="") as handle:
                accounts = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1500)
            self.assertEqual(len(accounts), 121)
            self.assertIn("Is Laundering", rows[0])
            self.assertIn("Payment Format", rows[0])
            self.assertIn("Account_1", rows[0])
            self.assertEqual(rows[0]["Account"], "8000F4580")

    def test_existing_file_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "HI-Small_Trans.csv"
            dest.write_text("existing contents")
            env = dict(os.environ, INSIGHTFORGE_DATA_DIR=directory)
            result = subprocess.run(
                [sys.executable, str(GENERATOR)],
                env=env, capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(dest.read_text(), "existing contents")


if __name__ == "__main__":
    unittest.main()
