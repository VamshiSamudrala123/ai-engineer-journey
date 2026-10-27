import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

project_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_dir))

from tool_registry import PROJECT_DIR, get_dataset_dir


class TestDatasetConfiguration(unittest.TestCase):

    def test_default_local_directory(self):
        with patch.dict(os.environ, {"INSIGHTFORGE_DATA_DIR": ""}):
            self.assertEqual(
                get_dataset_dir(),
                PROJECT_DIR / "data/raw",
            )

    def test_cloud_directory_override(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(
                os.environ,
                {"INSIGHTFORGE_DATA_DIR": folder},
            ):
                self.assertEqual(
                    get_dataset_dir(),
                    Path(folder),
                )

    def test_directory_whitespace_is_trimmed(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(
                os.environ,
                {"INSIGHTFORGE_DATA_DIR": f"  {folder}  "},
            ):
                self.assertEqual(
                    get_dataset_dir(),
                    Path(folder),
                )

    def test_relative_directory_is_rejected(self):
        with patch.dict(
            os.environ,
            {"INSIGHTFORGE_DATA_DIR": "relative/data"},
        ):
            with self.assertRaises(ValueError):
                get_dataset_dir()


if __name__ == "__main__":
    unittest.main()
