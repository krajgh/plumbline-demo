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
    tags: NotRequired[list[str]]  # absent when the task has none
    priority: NotRequired[str]  # "high" or "low"; absent means normal


PRIORITIES = ("high", "normal", "low")  # rank = index


def parse_date(text: str) -> datetime.date:
    """Parse a strict YYYY-MM-DD date. Raises ValueError for anything else."""
    # [0-9], not \d: \d also matches non-ASCII digits
    if not isinstance(text, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text):
        raise ValueError(f"invalid date: {text}")
    return datetime.date.fromisoformat(text)


def is_valid_tag(name: str) -> bool:
    """True if name is one or more of a-z, 0-9 and dash (ASCII only, no newline)."""
    return isinstance(name, str) and re.fullmatch(r"[a-z0-9-]+", name) is not None


def add_task(
    tasks: list[Task],
    title: str,
    due: str | None = None,
    tags: list[str] | None = None,
    priority: str = "normal",
) -> Task:
    """Append a new open task to tasks and return it.

    The new id is one more than the highest id in use, or 1 for an empty list.
    Surrounding whitespace is stripped from title. A blank title raises ValueError.
    due, if given, must be a YYYY-MM-DD date, else ValueError.
    tags, if given, must all be valid tags, else ValueError; duplicates are dropped.
    """
    title = title.strip()
    if not title:
        raise ValueError("title must not be empty")
    if due is not None:
        parse_date(due)
    for name in tags or []:
        if not is_valid_tag(name):
            raise ValueError(f"invalid tag: {name}")
    if priority not in PRIORITIES:
        raise ValueError(f"invalid priority: {priority}")
    next_id = max((task["id"] for task in tasks), default=0) + 1
    task: Task = {"id": next_id, "title": title, "done": False}
    if due is not None:
        task["due"] = due
    if tags:
        task["tags"] = list(dict.fromkeys(tags))
    if priority != "normal":
        task["priority"] = priority
    tasks.append(task)
    return task


def _find(tasks: list[Task], task_id: int) -> Task:
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise KeyError(task_id)


def edit_task(
    tasks: list[Task],
    task_id: int,
    title: str | None = None,
    due: str | None = None,
    no_due: bool = False,
    priority: str | None = None,
) -> Task:
    """Change the given fields of a task and return it.

    KeyError if no such id. ValueError (message ready to print) for a blank title, a bad date,
    a bad priority, due with no_due, or nothing to change; all checked before any change.
    Priority "normal" and no_due delete their keys.
    """
    task = _find(tasks, task_id)
    if title is None and due is None and not no_due and priority is None:
        raise ValueError("nothing to edit")
    if due is not None and no_due:
        raise ValueError("--due and --no-due cannot be used together")
    if title is not None:
        title = title.strip()
        if not title:
            raise ValueError("title must not be empty")
    if due is not None:
        try:
            parse_date(due)
        except ValueError:
            raise ValueError(f"invalid due date: {due}") from None
    if priority is not None and priority not in PRIORITIES:
        raise ValueError(f"invalid priority: {priority}")
    if title is not None:
        task["title"] = title
    if due is not None:
        task["due"] = due
    if no_due:
        task.pop("due", None)
    if priority == "normal":
        task.pop("priority", None)
    elif priority is not None:
        task["priority"] = priority
    return task


def remove_task(tasks: list[Task], task_id: int) -> Task:
    """Remove the task with task_id and return it. KeyError if no such id."""
    task = _find(tasks, task_id)
    tasks.remove(task)
    return task


def add_tag(tasks: list[Task], task_id: int, name: str) -> Task:
    """Add tag name to the task. ValueError if invalid (checked first), KeyError if no such id."""
    if not is_valid_tag(name):
        raise ValueError(f"invalid tag: {name}")
    task = _find(tasks, task_id)
    if name not in task.get("tags", []):
        task.setdefault("tags", []).append(name)
    return task


def remove_tag(tasks: list[Task], task_id: int, name: str) -> Task:
    """Remove tag name from the task. KeyError if no such id, ValueError if it lacks the tag."""
    task = _find(tasks, task_id)
    if name not in task.get("tags", []):
        raise ValueError(f"task {task_id} does not have tag {name}")
    task["tags"].remove(name)
    if not task["tags"]:
        del task["tags"]
    return task


def tagged_tasks(tasks: list[Task], name: str) -> list[Task]:
    """Return the tasks carrying tag name, in the given order."""
    return [task for task in tasks if name in task.get("tags", [])]


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
    """Return the tasks to display, by priority then id: open tasks only, unless show_all.

    Stored priorities must already be valid (the CLI checks them first).
    """
    shown = tasks if show_all else [task for task in tasks if not task["done"]]
    return sorted(shown, key=lambda task: (PRIORITIES.index(task.get("priority", "normal")), task["id"]))


def task_stats(
    tasks: list[Task], today: datetime.date, tag: str | None = None
) -> tuple[dict[str, int], dict[str, int]]:
    """Return (counts, per-tag open counts); the latter is empty when tag is given.

    counts has open, done, high, normal, low and overdue. Stored values must already be valid.
    """
    if tag is not None:
        tasks = tagged_tasks(tasks, tag)
    open_tasks = [task for task in tasks if not task["done"]]
    counts = {
        "open": len(open_tasks),
        "done": len(tasks) - len(open_tasks),
        **{p: sum(t.get("priority", "normal") == p for t in open_tasks) for p in PRIORITIES},
        "overdue": len(overdue_tasks(open_tasks, today)),
    }
    per_tag: dict[str, int] = {}
    if tag is None:
        for task in open_tasks:
            for name in set(task.get("tags", [])):
                per_tag[name] = per_tag.get(name, 0) + 1
    return counts, dict(sorted(per_tag.items(), key=lambda item: (-item[1], item[0])))


def overdue_tasks(tasks: list[Task], today: datetime.date) -> list[Task]:
    """Return the open tasks due before today, ordered by due date, then id."""
    late = [
        task
        for task in tasks
        if not task["done"] and "due" in task and parse_date(task["due"]) < today
    ]
    return sorted(late, key=lambda task: (task["due"], task["id"]))
