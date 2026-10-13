"""Read the task list and distribute pending work across study days."""

import copy
import json
import os
from pathlib import Path
import tempfile

from tools import calculate_study_time


SAMPLE_TASKS = Path(__file__).with_name("tasks.json")
LOCAL_TASKS = Path(__file__).with_name("tasks.local.json")


class TaskError(Exception):
    """A task-file problem with a safe, useful message."""


def validate_tasks(tasks):
    if not isinstance(tasks, list) or len(tasks) > 50:
        raise TaskError("Tasks must be a JSON list with at most 50 entries.")
    ids = set()
    for task in tasks:
        if not isinstance(task, dict) or set(task) != {"id", "title", "estimated_minutes", "done"}:
            raise TaskError("Each task needs id, title, estimated_minutes, and done.")
        task_id = task["id"]
        if not isinstance(task_id, str) or not task_id.strip() or len(task_id) > 50 or task_id in ids:
            raise TaskError("Task IDs must be unique, nonempty strings of at most 50 characters.")
        ids.add(task_id)
        if not isinstance(task["title"], str) or not task["title"].strip() or len(task["title"]) > 200:
            raise TaskError("Task titles must contain 1 to 200 characters.")
        if type(task["estimated_minutes"]) is not int or not 1 <= task["estimated_minutes"] <= 1440:
            raise TaskError("Task estimates must be whole minutes between 1 and 1440.")
        if type(task["done"]) is not bool:
            raise TaskError("Task done values must be true or false.")
    return tasks


def load_tasks(path):
    try:
        # Keep accidental large files out of the prompt and the planner.
        if path.stat().st_size > 100_000:
            raise TaskError("The task file is too large; use at most 50 small tasks.")
        return validate_tasks(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise TaskError("Could not read the task file. Check its location and JSON format.") from None


def local_task_store(path=LOCAL_TASKS):
    """Make a personal copy once; never overwrite an existing task file."""
    path = Path(path)
    seed = load_tasks(SAMPLE_TASKS)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(seed, handle, indent=2)
            handle.write("\n")
    except FileExistsError:
        pass
    except OSError:
        raise TaskError("Could not create the local task file. Check folder permissions.") from None
    return TaskStore.from_file(path)


class TaskStore:
    def __init__(self, tasks, path=None):
        self.tasks = copy.deepcopy(validate_tasks(tasks))
        self.path = path

    @classmethod
    def from_file(cls, path=SAMPLE_TASKS):
        path = Path(path)
        return cls(load_tasks(path), path)

    def all_tasks(self):
        if self.path is not None:
            self.tasks = load_tasks(self.path)
        return copy.deepcopy(self.tasks)

    def list_pending_tasks(self):
        return {"tasks": [task for task in self.all_tasks() if not task["done"]]}

    def prepare_completion(self, task_id):
        if not isinstance(task_id, str) or not task_id.strip():
            raise TaskError("Provide a nonempty task ID.")
        for task in self.all_tasks():
            if task["id"] == task_id:
                return task
        raise TaskError("No task has that ID. Read the task list first.")

    def complete_task(self, expected_task, *, confirmed=False):
        # Confirmation comes from the interface, never from model arguments.
        if confirmed is not True:
            raise TaskError("Task completion needs explicit confirmation.")
        tasks = self.all_tasks()
        for task in tasks:
            if task["id"] == expected_task.get("id"):
                if task != expected_task:
                    raise TaskError("This task changed after the preview. Request a fresh update.")
                if task["done"]:
                    return {"status": "already_done", "task": task}
                task["done"] = True
                self._save(tasks)
                return {"status": "completed", "task": copy.deepcopy(task)}
        raise TaskError("This task was removed. Request a fresh update.")

    def _save(self, tasks):
        if self.path is not None:
            temporary = None
            try:
                # Replace the whole file only after a complete JSON write.
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                                 prefix=".tasks-", suffix=".tmp", delete=False) as handle:
                    temporary = Path(handle.name)
                    json.dump(tasks, handle, indent=2)
                    handle.write("\n")
                os.replace(temporary, self.path)
            except OSError:
                raise TaskError("Could not save tasks. Check folder permissions.") from None
            finally:
                if temporary is not None:
                    try:
                        temporary.unlink(missing_ok=True)
                    except OSError:
                        pass
        self.tasks = copy.deepcopy(tasks)

    def build_study_plan(self, minutes_per_day, days):
        available = calculate_study_time(minutes_per_day, days)
        pending = self.list_pending_tasks()["tasks"]
        remaining = {task["id"]: task["estimated_minutes"] for task in pending}
        sessions = []
        for day in range(1, days + 1):
            budget = minutes_per_day
            work = []
            for task in pending:
                amount = min(budget, remaining[task["id"]])
                if amount:
                    work.append({"id": task["id"], "title": task["title"], "minutes": amount})
                    remaining[task["id"]] -= amount
                    budget -= amount
                if not budget:
                    break
            sessions.append({"day": day, "tasks": work, "unused_minutes": budget})
        unscheduled = [
            {"id": task["id"], "title": task["title"], "remaining_minutes": remaining[task["id"]]}
            for task in pending if remaining[task["id"]]
        ]
        return {**available, "sessions": sessions, "unscheduled": unscheduled}
