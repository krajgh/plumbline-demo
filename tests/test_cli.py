"""Tests for tasklist.cli, driven through main() the way the command line does."""

import subprocess
import sys
from pathlib import Path

import pytest

from tasklist import store
from tasklist.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TASKS = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Call Sam", "done": True},
]


@pytest.fixture
def tasks_file(tmp_path):
    """A task file holding one open task and one finished task."""
    path = tmp_path / "tasks.json"
    store.save(path, TASKS)
    return path


def run(path, *args):
    """Call main() with --file pointing at path and return its exit status."""
    return main(["--file", str(path), *args])


def test_add_prints_the_new_id_and_saves_the_task(tasks_file, capsys):
    assert run(tasks_file, "add", "Pay rent") == 0

    assert capsys.readouterr().out == "added 3\n"
    assert store.load(tasks_file) == [
        *TASKS,
        {"id": 3, "title": "Pay rent", "done": False},
    ]


def test_add_with_an_empty_title_is_an_error(tasks_file, capsys):
    assert run(tasks_file, "add", "  ") == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: title must not be empty\n"
    assert store.load(tasks_file) == TASKS


def test_done_marks_the_task_done_and_prints_its_id(tasks_file, capsys):
    assert run(tasks_file, "done", "1") == 0

    assert capsys.readouterr().out == "done 1\n"
    assert store.load(tasks_file)[0] == {"id": 1, "title": "Buy milk", "done": True}


def test_done_with_an_unknown_id_is_an_error(tasks_file, capsys):
    assert run(tasks_file, "done", "99") == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: no task with id 99\n"
    assert store.load(tasks_file) == TASKS


def test_list_hides_finished_tasks_unless_all_is_given(tasks_file, capsys):
    assert run(tasks_file, "list") == 0
    assert capsys.readouterr().out == "[ ] 1 Buy milk\n"

    assert run(tasks_file, "list", "--all") == 0
    assert capsys.readouterr().out == "[ ] 1 Buy milk\n[x] 2 Call Sam\n"


def test_tasklist_file_environment_variable_selects_the_file(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "from_env.json"  # does not exist yet
    monkeypatch.setenv("TASKLIST_FILE", str(path))

    assert main(["add", "Buy milk"]) == 0
    assert main(["list"]) == 0

    assert capsys.readouterr().out == "added 1\n[ ] 1 Buy milk\n"
    assert store.load(path) == [{"id": 1, "title": "Buy milk", "done": False}]


def test_python_dash_m_exits_with_the_status_from_main(tasks_file):
    result = subprocess.run(
        [sys.executable, "-m", "tasklist", "--file", str(tasks_file), "done", "99"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stderr == "error: no task with id 99\n"
