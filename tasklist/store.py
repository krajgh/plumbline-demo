"""Load and save the task list as a JSON file."""

import json
import os
import tempfile
from pathlib import Path

from tasklist.core import Task

ENV_VAR = "TASKLIST_FILE"
DEFAULT_FILE = "tasks.json"


def resolve_path(file_arg: str | None = None) -> Path:
    """Return the task file to use: file_arg, else $TASKLIST_FILE, else tasks.json."""
    return Path(file_arg or os.environ.get(ENV_VAR) or DEFAULT_FILE)


def load(path: Path | str) -> list[Task]:
    """Return the tasks stored at path, or an empty list if there is no such file."""
    try:
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save(path: Path | str, tasks: list[Task]) -> None:
    """Write tasks to path as JSON, atomically.

    The JSON goes to a temporary file in the same folder first, and os.replace then
    moves it over path in one step. If anything fails on the way, the old file is
    left untouched and the temporary file is removed.
    """
    path = Path(path)
    fd, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f"{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(tasks, file, indent=2, sort_keys=True)
            file.write("\n")
        os.replace(temp_name, path)
    except BaseException:
        os.unlink(temp_name)
        raise
