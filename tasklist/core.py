"""Task-list operations. They work on a list in memory and never touch the disk."""

import datetime
import re
from typing import NotRequired, TypedDict


class Task(TypedDict):
    """One to-do item, as it is stored in the JSON file."""

    id: int
    title: str
    done: bool
    due: NotRequired[str]  # ISO date, YYYY-MM-DD; absent when the task has none


def parse_date(text: str) -> datetime.date:
    """Parse a strict YYYY-MM-DD date. Raises ValueError for anything else."""
    # [0-9], not \d: \d also matches non-ASCII digits
    if not isinstance(text, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text):
        raise ValueError(f"invalid date: {text}")
    return datetime.date.fromisoformat(text)


def add_task(tasks: list[Task], title: str, due: str | None = None) -> Task:
    """Append a new open task to tasks and return it.

    The new id is one more than the highest id in use, or 1 for an empty list.
    Surrounding whitespace is stripped from title. A blank title raises ValueError.
    due, if given, must be a YYYY-MM-DD date, else ValueError.
    """
    title = title.strip()
    if not title:
        raise ValueError("title must not be empty")
    if due is not None:
        parse_date(due)
    next_id = max((task["id"] for task in tasks), default=0) + 1
    task: Task = {"id": next_id, "title": title, "done": False}
    if due is not None:
        task["due"] = due
    tasks.append(task)
    return task


def complete_task(tasks: list[Task], task_id: int) -> Task:
    """Mark the task with task_id as done and return it.

    Raises KeyError if no task has that id.
    """
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            return task
    raise KeyError(task_id)


def visible_tasks(tasks: list[Task], show_all: bool = False) -> list[Task]:
    """Return the tasks to display, in id order: open tasks only, unless show_all."""
    shown = tasks if show_all else [task for task in tasks if not task["done"]]
    return sorted(shown, key=lambda task: task["id"])


def overdue_tasks(tasks: list[Task], today: datetime.date) -> list[Task]:
    """Return the open tasks due before today, ordered by due date, then id."""
    late = [
        task
        for task in tasks
        if not task["done"] and "due" in task and parse_date(task["due"]) < today
    ]
    return sorted(late, key=lambda task: (task["due"], task["id"]))
