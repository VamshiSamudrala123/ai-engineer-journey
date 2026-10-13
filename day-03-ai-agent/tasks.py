"""Read the task list and distribute pending work across study days."""

import copy
import json
from pathlib import Path

from tools import calculate_study_time


SAMPLE_TASKS = Path(__file__).with_name("tasks.json")


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
