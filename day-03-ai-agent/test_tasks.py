import copy
import json
from pathlib import Path
import tempfile
import unittest

from tasks import TaskError, TaskStore, load_tasks, validate_tasks


SAMPLE = [
    {"id": "a", "title": "Read", "estimated_minutes": 90, "done": False},
    {"id": "b", "title": "Test", "estimated_minutes": 45, "done": False},
    {"id": "c", "title": "Setup", "estimated_minutes": 10, "done": True},
]


class TaskTests(unittest.TestCase):
    def test_only_pending_tasks_are_returned(self):
        store = TaskStore(SAMPLE)
        self.assertEqual([task["id"] for task in store.list_pending_tasks()["tasks"]], ["a", "b"])

    def test_plan_splits_long_tasks_and_reports_remaining_work(self):
        store = TaskStore(SAMPLE)
        plan = store.build_study_plan(60, 2)
        self.assertEqual(plan["sessions"][0]["tasks"][0]["minutes"], 60)
        self.assertEqual([task["minutes"] for task in plan["sessions"][1]["tasks"]], [30, 30])
        self.assertEqual(plan["unscheduled"][0]["remaining_minutes"], 15)
        self.assertEqual(store.all_tasks(), SAMPLE)

    def test_plan_never_exceeds_daily_budget(self):
        for minutes, days in ((1, 3), (45, 3), (90, 5)):
            plan = TaskStore(SAMPLE).build_study_plan(minutes, days)
            scheduled = 0
            for session in plan["sessions"]:
                used = sum(task["minutes"] for task in session["tasks"])
                self.assertEqual(used + session["unused_minutes"], minutes)
                scheduled += used
            self.assertEqual(scheduled + sum(task["remaining_minutes"] for task in plan["unscheduled"]), 135)

    def test_empty_tasks_leave_time_available(self):
        plan = TaskStore([]).build_study_plan(90, 1)
        self.assertEqual(plan["sessions"][0]["unused_minutes"], 90)
        self.assertEqual(plan["unscheduled"], [])

    def test_bad_json_missing_and_invalid_utf8_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tasks.json"
            with self.assertRaises(TaskError):
                load_tasks(path)
            for content in (b"invalid json", b"\xff", b"{}"):
                path.write_bytes(content)
                with self.assertRaises(TaskError):
                    load_tasks(path)

    def test_duplicate_ids_and_bad_fields_are_rejected(self):
        variants = [SAMPLE + [SAMPLE[0]], ["a"], {"tasks": []}]
        for field, value in (("id", ""), ("title", ""), ("estimated_minutes", True), ("done", "false")):
            changed = copy.deepcopy(SAMPLE)
            changed[0][field] = value
            variants.append(changed)
        for value in variants:
            with self.assertRaises(TaskError):
                validate_tasks(value)

    def test_returned_tasks_are_copies(self):
        store = TaskStore(SAMPLE)
        store.all_tasks()[0]["title"] = "Changed"
        self.assertEqual(store.all_tasks()[0]["title"], "Read")

    def test_file_store_reads_external_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tasks.json"
            path.write_text(json.dumps(SAMPLE), encoding="utf-8")
            store = TaskStore.from_file(path)
            path.write_text("[]", encoding="utf-8")
            self.assertEqual(store.all_tasks(), [])


if __name__ == "__main__":
    unittest.main()
