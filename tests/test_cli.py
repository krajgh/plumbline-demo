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


# --- due dates ---

DATED = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Pay rent", "done": False, "due": "2026-10-01"},
    {"id": 3, "title": "Call Sam", "done": True, "due": "2026-01-05"},
]

OVERDUE = [
    {"id": 1, "title": "a", "done": False, "due": "2026-09-30"},
    {"id": 2, "title": "b", "done": False, "due": "2026-09-01"},
    {"id": 3, "title": "c", "done": False, "due": "2026-10-01"},
    {"id": 4, "title": "d", "done": False, "due": "2026-12-01"},
    {"id": 5, "title": "e", "done": False},
    {"id": 6, "title": "f", "done": True, "due": "2026-08-01"},
    {"id": 7, "title": "g", "done": False, "due": "2026-09-01"},
]


def test_ac1_add_with_due_stores_the_date_and_without_stores_no_key(tmp_path, capsys):
    path = tmp_path / "tasks.json"

    assert run(path, "add", "Pay rent", "--due", "2026-10-01") == 0
    assert capsys.readouterr().out == "added 1\n"
    assert run(path, "add", "Buy milk") == 0

    assert store.load(path) == [
        {"id": 1, "title": "Pay rent", "done": False, "due": "2026-10-01"},
        {"id": 2, "title": "Buy milk", "done": False},
    ]


@pytest.mark.parametrize(
    "value", ["2026-02-30", "tomorrow", "2026-2-3", "20261001", "2026-13-01", ""]
)
def test_ac2_add_with_a_bad_due_is_an_error_and_changes_nothing(
    tasks_file, tmp_path, capsys, value
):
    assert run(tasks_file, "add", "X", "--due", value) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"error: invalid due date: {value}\n"
    assert store.load(tasks_file) == TASKS

    missing = tmp_path / "new.json"
    assert run(missing, "add", "X", "--due", value) == 2
    assert not missing.exists()


def test_ac2_add_accepts_a_leap_day(tmp_path):
    path = tmp_path / "t.json"

    assert run(path, "add", "X", "--due", "2028-02-29") == 0
    assert store.load(path)[0].get("due") == "2028-02-29"


def test_ac3_list_shows_the_due_date_of_dated_tasks(tmp_path, capsys):
    path = tmp_path / "tasks.json"
    store.save(path, DATED)

    assert run(path, "list") == 0
    assert capsys.readouterr().out == "[ ] 1 Buy milk\n[ ] 2 Pay rent (due 2026-10-01)\n"

    assert run(path, "list", "--all") == 0
    assert capsys.readouterr().out == (
        "[ ] 1 Buy milk\n[ ] 2 Pay rent (due 2026-10-01)\n"
        "[x] 3 Call Sam (due 2026-01-05)\n"
    )


def test_ac4_list_overdue_shows_open_past_due_tasks_ordered(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "tasks.json"
    store.save(path, OVERDUE)
    monkeypatch.setenv("TASKLIST_TODAY", "2026-10-01")
    expected = (
        "[ ] 2 b (due 2026-09-01)\n[ ] 7 g (due 2026-09-01)\n[ ] 1 a (due 2026-09-30)\n"
    )

    assert run(path, "list", "--overdue") == 0
    assert capsys.readouterr().out == expected
    assert run(path, "list", "--overdue", "--all") == 0
    assert capsys.readouterr().out == expected

    monkeypatch.setenv("TASKLIST_TODAY", "2026-01-01")
    assert run(path, "list", "--overdue") == 0
    assert capsys.readouterr().out == ""


def test_ac5_today_comes_from_the_environment_and_a_bad_value_is_an_error(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "tasks.json"
    store.save(
        path, [{"id": 1, "title": "Pay rent", "done": False, "due": "2026-10-01"}]
    )

    monkeypatch.setenv("TASKLIST_TODAY", "2026-09-30")
    assert run(path, "list", "--overdue") == 0
    assert capsys.readouterr().out == ""
    monkeypatch.setenv("TASKLIST_TODAY", "2026-10-02")
    assert run(path, "list", "--overdue") == 0
    assert capsys.readouterr().out == "[ ] 1 Pay rent (due 2026-10-01)\n"

    monkeypatch.setenv("TASKLIST_TODAY", "notadate")
    assert run(path, "list", "--overdue") == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: invalid TASKLIST_TODAY: notadate\n"

    assert run(path, "list") == 0  # plain list never reads it


def test_ac6_a_010_file_keeps_working_and_done_adds_no_due_key(
    tasks_file, monkeypatch, capsys
):
    monkeypatch.setenv("TASKLIST_TODAY", "2026-10-01")

    assert run(tasks_file, "list") == 0
    assert capsys.readouterr().out == "[ ] 1 Buy milk\n"
    assert run(tasks_file, "list", "--all") == 0
    assert capsys.readouterr().out == "[ ] 1 Buy milk\n[x] 2 Call Sam\n"
    assert run(tasks_file, "list", "--overdue") == 0
    assert capsys.readouterr().out == ""

    assert run(tasks_file, "done", "1") == 0
    assert store.load(tasks_file) == [{**TASKS[0], "done": True}, TASKS[1]]


# --- malformed stored due date under list --overdue ---


def run_overdue_with_bad_due(tmp_path):
    """Run list --overdue on a file whose open task 1 has due "soon"; return (status, exception)."""
    path = tmp_path / "tasks.json"
    store.save(path, [{"id": 1, "title": "a", "done": False, "due": "soon"}])
    try:
        return run(path, "list", "--overdue"), None
    except Exception as exc:  # today's code may crash; the test asserts it does not
        return None, exc


@pytest.mark.parametrize("today", [None, "2026-10-01"])
def test_ac1_overdue_with_a_malformed_stored_due_names_the_task(
    tmp_path, monkeypatch, capsys, today
):
    if today is None:
        monkeypatch.delenv("TASKLIST_TODAY", raising=False)
    else:
        monkeypatch.setenv("TASKLIST_TODAY", today)

    status, exc = run_overdue_with_bad_due(tmp_path)

    assert exc is None, f"main() raised {exc!r}"
    assert status == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.splitlines()
    assert len(lines) == 1
    assert "1" in lines[0] and "soon" in lines[0]
    assert "TASKLIST_TODAY" not in lines[0]
