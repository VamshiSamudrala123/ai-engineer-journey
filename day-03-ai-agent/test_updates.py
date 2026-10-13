import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tasks import TaskError, TaskStore, local_task_store
from test_tasks import SAMPLE


class UpdateTests(unittest.TestCase):
    def test_completion_requires_explicit_confirmation(self):
        store = TaskStore(SAMPLE)
        for confirmed in (False, None, "yes", 1):
            with self.assertRaises(TaskError):
                store.complete_task(store.prepare_completion("a"), confirmed=confirmed)
        self.assertFalse(store.all_tasks()[0]["done"])

    def test_approved_completion_changes_only_one_task(self):
        store = TaskStore(SAMPLE)
        result = store.complete_task(store.prepare_completion("a"), confirmed=True)
        self.assertEqual(result["status"], "completed")
        expected = copy.deepcopy(SAMPLE)
        expected[0]["done"] = True
        self.assertEqual(store.all_tasks(), expected)

    def test_unknown_task_is_rejected(self):
        with self.assertRaises(TaskError):
            TaskStore(SAMPLE).prepare_completion("missing")

    def test_changed_preview_cannot_be_applied(self):
        store = TaskStore(SAMPLE)
        preview = store.prepare_completion("a")
        store.tasks[0]["title"] = "New title"
        with self.assertRaisesRegex(TaskError, "changed"):
            store.complete_task(preview, confirmed=True)
        self.assertFalse(store.all_tasks()[0]["done"])

    def test_file_completion_survives_reload(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tasks.json"
            path.write_text(json.dumps(SAMPLE), encoding="utf-8")
            store = TaskStore.from_file(path)
            store.complete_task(store.prepare_completion("a"), confirmed=True)
            self.assertTrue(TaskStore.from_file(path).all_tasks()[0]["done"])
            self.assertEqual(list(Path(folder).glob(".tasks-*.tmp")), [])

    def test_failed_save_preserves_original_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tasks.json"
            original = json.dumps(SAMPLE)
            path.write_text(original, encoding="utf-8")
            store = TaskStore.from_file(path)
            with patch("tasks.os.replace", side_effect=OSError("private details")):
                with self.assertRaises(TaskError):
                    store.complete_task(store.prepare_completion("a"), confirmed=True)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertEqual(list(Path(folder).glob(".tasks-*.tmp")), [])

    def test_local_copy_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tasks.local.json"
            store = local_task_store(path)
            task = store.list_pending_tasks()["tasks"][0]
            store.complete_task(task, confirmed=True)
            self.assertTrue(local_task_store(path).all_tasks()[0]["done"])

    def test_browser_stores_do_not_share_updates(self):
        first, second = TaskStore(SAMPLE), TaskStore(SAMPLE)
        first.complete_task(first.prepare_completion("a"), confirmed=True)
        self.assertFalse(second.all_tasks()[0]["done"])


if __name__ == "__main__":
    unittest.main()
