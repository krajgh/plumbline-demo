"""Tests for the edit and remove commands (AC-1 .. AC-6)."""

import copy
import json

import pytest

from tasklist import store
from tasklist.cli import main

FULL = {"id": 1, "title": "a", "done": True, "due": "2026-10-01", "tags": ["x"], "priority": "high"}


def run(path, *args):
    return main(["--file", str(path), *args])


def saved(tmp_path, tasks):
    path = tmp_path / "tasks.json"
    store.save(path, copy.deepcopy(tasks))
    return path


def assert_error(path, capsys, before, err=None, *args):
    """Run args; expect exit 2, one 'error: ' stderr line (exactly err if given), file unchanged."""
    assert run(path, *args) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.splitlines()
    assert len(lines) == 1 and lines[0].startswith("error: ")
    if err is not None:
        assert captured.err == err + "\n"
    assert path.read_bytes() == before


def test_ac1_edit_title_strips_and_keeps_other_keys(tmp_path, capsys):
    other = {"id": 2, "title": "b", "done": False}
    path = saved(tmp_path, [FULL, other])

    assert run(path, "edit", "1", "--title", "  New  ") == 0

    assert capsys.readouterr().out == "edited 1\n"
    assert store.load(path) == [{**FULL, "title": "New"}, other]


@pytest.mark.parametrize("title", ["   ", ""])
def test_ac1_blank_or_empty_title_is_an_error(tmp_path, capsys, title):
    path = saved(tmp_path, [FULL])
    assert_error(path, capsys, path.read_bytes(), "error: title must not be empty", "edit", "1", "--title", title)


def test_ac2_due_set_replace_and_no_due(tmp_path, capsys):
    other = {"id": 2, "title": "b", "done": False, "due": "2026-01-01", "tags": ["y"]}
    path = saved(tmp_path, [FULL, other])
    no_due = {k: v for k, v in FULL.items() if k != "due"}

    assert run(path, "edit", "1", "--due", "2026-12-01") == 0
    assert store.load(path) == [{**FULL, "due": "2026-12-01"}, other]
    assert run(path, "edit", "1", "--due", "2027-01-02") == 0
    assert store.load(path) == [{**FULL, "due": "2027-01-02"}, other]
    assert run(path, "edit", "1", "--no-due") == 0
    assert store.load(path) == [no_due, other]
    assert run(path, "edit", "1", "--no-due") == 0
    assert store.load(path) == [no_due, other]
    assert capsys.readouterr().out == "edited 1\n" * 4


@pytest.mark.parametrize("due", ["2026-02-30", "abc", ""])
def test_ac2_invalid_due_is_an_error(tmp_path, capsys, due):
    path = saved(tmp_path, [FULL])
    assert_error(path, capsys, path.read_bytes(), f"error: invalid due date: {due}", "edit", "1", "--due", due)


def test_ac2_due_with_no_due_is_an_error(tmp_path, capsys):
    path = saved(tmp_path, [FULL])
    assert_error(path, capsys, path.read_bytes(), None, "edit", "1", "--due", "2026-12-01", "--no-due")


def test_ac3_priority_high_low_and_normal(tmp_path):
    other = {"id": 2, "title": "b", "done": False, "priority": "low", "tags": ["y"]}
    path = saved(tmp_path, [{**FULL, "priority": "low"}, other])
    no_prio = {k: v for k, v in FULL.items() if k != "priority"}

    assert run(path, "edit", "1", "--priority", "high") == 0
    assert store.load(path) == [FULL, other]
    assert run(path, "edit", "1", "--priority", "low") == 0
    assert store.load(path) == [{**FULL, "priority": "low"}, other]
    assert run(path, "edit", "1", "--priority", "normal") == 0
    assert store.load(path) == [no_prio, other]
    assert run(path, "edit", "1", "--priority", "normal") == 0
    assert store.load(path) == [no_prio, other]


def test_ac3_invalid_priority_is_an_error(tmp_path, capsys):
    path = saved(tmp_path, [FULL])
    assert_error(path, capsys, path.read_bytes(), "error: invalid priority: urgent", "edit", "1", "--priority", "urgent")


def test_ac4_no_field_and_unknown_id_are_errors(tmp_path, capsys):
    path = saved(tmp_path, [FULL])
    before = path.read_bytes()
    assert_error(path, capsys, before, None, "edit", "1")
    assert_error(path, capsys, before, "error: no task with id 99", "edit", "99", "--title", "x")
    # an unknown id is reported before a bad value
    assert_error(path, capsys, before, "error: no task with id 99", "edit", "99", "--priority", "urgent")


@pytest.mark.parametrize("bad", [("--priority", "urgent"), ("--due", "nope"), ("--due", "")])
def test_ac4_a_bad_value_leaves_no_partial_edit(tmp_path, capsys, bad):
    path = saved(tmp_path, [FULL])
    assert_error(path, capsys, path.read_bytes(), None, "edit", "1", "--title", "New", *bad)


def test_ac4_edit_task_raises_before_mutating():
    from tasklist import core

    tasks = [copy.deepcopy(FULL)]
    for kwargs in ({"priority": "urgent"}, {"due": "nope"}, {"due": "2026-12-01", "no_due": True}, {"title": " "}):
        with pytest.raises(ValueError):
            core.edit_task(tasks, 1, **{"title": "New", **kwargs})
        assert tasks == [FULL]
    with pytest.raises(KeyError):
        core.edit_task(tasks, 99, title="x")


def test_ac5_remove_keeps_ids_and_next_add_is_max_plus_one(tmp_path, capsys):
    path = saved(tmp_path, [{"id": i, "title": f"t{i}", "done": False} for i in (1, 2, 3)])

    assert run(path, "remove", "2") == 0
    assert capsys.readouterr().out == "removed 2\n"
    assert [t["id"] for t in store.load(path)] == [1, 3]
    assert run(path, "add", "z") == 0
    assert capsys.readouterr().out == "added 4\n"
    assert run(path, "remove", "4") == 0 and run(path, "remove", "3") == 0
    capsys.readouterr()
    assert run(path, "add", "y") == 0
    assert capsys.readouterr().out == "added 2\n"


def test_ac5_remove_unknown_id_is_an_error(tmp_path, capsys):
    path = saved(tmp_path, [FULL])
    assert_error(path, capsys, path.read_bytes(), "error: no task with id 9", "remove", "9")


def test_ac5_remove_task_removes_and_returns():
    from tasklist import core

    tasks = [{"id": 1, "title": "a", "done": False}, {"id": 2, "title": "b", "done": False}]
    assert core.remove_task(tasks, 1)["id"] == 1
    assert [t["id"] for t in tasks] == [2]
    with pytest.raises(KeyError):
        core.remove_task(tasks, 9)
    assert [t["id"] for t in tasks] == [2]


def test_ac6_legacy_file_lists_completes_and_edits_without_new_keys(tmp_path, capsys):
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps([{"id": 1, "title": "a", "done": False}]))

    assert run(path, "list") == 0
    assert capsys.readouterr().out == "[ ] 1 a\n"
    for args in (("--title", "b"), ("--priority", "normal"), ("--no-due",)):
        assert run(path, "edit", "1", *args) == 0
    assert json.loads(path.read_text()) == [{"id": 1, "title": "b", "done": False}]
    assert run(path, "done", "1") == 0
    assert json.loads(path.read_text())[0]["done"] is True
