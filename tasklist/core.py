"""Task-list operations. They work on a list in memory and never touch the disk."""

from typing import TypedDict


class Task(TypedDict):
    """One to-do item, as it is stored in the JSON file."""

    id: int
    title: str
    done: bool


def add_task(tasks: list[Task], title: str) -> Task:
    """Append a new open task to tasks and return it.

    The new id is one more than the highest id in use, or 1 for an empty list.
    Surrounding whitespace is stripped from title. A blank title raises ValueError.
    """
    title = title.strip()
    if not title:
        raise ValueError("title must not be empty")
    next_id = max((task["id"] for task in tasks), default=0) + 1
    task: Task = {"id": next_id, "title": title, "done": False}
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
