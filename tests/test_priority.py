"""Tests for priorities: add --priority, ordering, the ! marker, stored-data safety."""

import pytest

from tasklist import store
from tasklist.cli import main


def run(path, *args):
    return main(["--file", str(path), *args])


def task(id, priority="MISSING", done=False, **extra):
    t = {"id": id, "title": f"T{id}", "done": done, **extra}
    if priority != "MISSING":
        t["priority"] = priority
    return t


def saved(tmp_path, tasks):
    path = tmp_path / "tasks.json"
    store.save(path, tasks)
    return path


def ids(capsys):
    return [line[4:].split()[0] for line in capsys.readouterr().out.splitlines()]


def test_ac1_add_stores_priority_only_when_not_normal(tmp_path, capsys):
    path = tmp_path / "tasks.json"
    for args in (["--priority", "high"], ["--priority", "low"], ["--priority", "normal"], []):
        assert run(path, "add", "X", *args) == 0
    assert capsys.readouterr().out == "".join(f"added {n}\n" for n in (1, 2, 3, 4))
    assert [t.get("priority") for t in store.load(path)] == ["high", "low", None, None]
    assert "priority" not in store.load(path)[2]


def test_ac1_core_add_task_priority():
    from tasklist import core

    tasks = []
    assert core.add_task(tasks, "a", priority="high")["priority"] == "high"
    assert "priority" not in core.add_task(tasks, "b")
    assert "priority" not in core.add_task(tasks, "c", priority="normal")


@pytest.mark.parametrize("bad", ["urgent", "HIGH", ""])
def test_ac2_add_invalid_priority_is_refused(tmp_path, capsys, bad):
    path = saved(tmp_path, [task(1)])
    raw = path.read_bytes()

    assert run(path, "add", "A", "--priority", bad) == 2

    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", f"error: invalid priority: {bad}\n")
    assert path.read_bytes() == raw


def test_ac2_invalid_priority_creates_no_file(tmp_path):
    path = tmp_path / "new.json"
    assert run(path, "add", "A", "--priority", "urgent") == 2
    assert not path.exists()


def test_ac2_core_add_task_raises_and_leaves_list():
    from tasklist import core

    tasks = []
    with pytest.raises(ValueError):
        core.add_task(tasks, "A", priority="urgent")
    assert tasks == []


def test_ac3_list_orders_open_tasks_by_priority_then_id(tmp_path, capsys):
    path = saved(tmp_path, [task(1, "low"), task(2, "normal"), task(3, "high"), task(4, "high"), task(5)])
    assert run(path, "list") == 0
    assert ids(capsys) == ["3", "4", "2", "5", "1"]


def test_ac4_high_tasks_get_a_marker_and_others_do_not(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("TASKLIST_TODAY", "2026-10-05")
    path = saved(tmp_path, [
        task(1, "high"),
        task(2, "high", due="2026-10-01", tags=["home"]),
        task(3, "normal"),
        task(4, "low"),
        task(5),
        task(6, "high", done=True),
    ])
    assert run(path, "list", "--all") == 0
    assert capsys.readouterr().out == (
        "[ ] 1 ! T1\n[ ] 2 ! T2 (due 2026-10-01) #home\n[x] 6 ! T6\n[ ] 3 T3\n[ ] 5 T5\n[ ] 4 T4\n"
    )
    assert run(path, "list", "--overdue") == 0
    assert capsys.readouterr().out == "[ ] 2 ! T2 (due 2026-10-01) #home\n"
    assert run(path, "list", "--tag", "home") == 0
    assert capsys.readouterr().out == "[ ] 2 ! T2 (due 2026-10-01) #home\n"


def test_ac5_all_orders_done_and_open_together_by_priority_then_id(tmp_path, capsys):
    path = saved(tmp_path, [
        task(1, "low", done=True), task(2, "low"), task(3, "high", done=True), task(4, "high"), task(5),
    ])
    assert run(path, "list", "--all") == 0
    assert ids(capsys) == ["3", "4", "5", "1", "2"]


def test_ac5_all_without_priorities_is_plain_id_order(tmp_path, capsys):
    path = saved(tmp_path, [task(1, done=True), task(2), task(3)])
    assert run(path, "list", "--all") == 0
    assert ids(capsys) == ["1", "2", "3"]


def test_ac5_core_visible_tasks_order():
    from tasklist import core

    tasks = [
        task(1, "low", done=True), task(2, "low"), task(3, "high", done=True), task(4, "high"), task(5),
    ]
    assert [t["id"] for t in core.visible_tasks(tasks, show_all=True)] == [3, 4, 5, 1, 2]
    assert [t["id"] for t in core.visible_tasks(tasks)] == [4, 5, 2]


def test_ac6_overdue_ignores_priority_and_tag_keeps_priority_order(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("TASKLIST_TODAY", "2026-10-05")
    path = saved(tmp_path, [
        task(1, "high", due="2026-10-03"), task(2, due="2026-10-01"),
        task(3, "low", tags=["work"]), task(4, "high", tags=["work"]),
    ])
    assert run(path, "list", "--overdue") == 0
    assert ids(capsys) == ["2", "1"]
    assert run(path, "list", "--tag", "work") == 0
    assert ids(capsys) == ["4", "3"]


def test_ac6_all_with_tag_follows_all_order(tmp_path, capsys):
    path = saved(tmp_path, [
        task(1, "low", tags=["work"]), task(2, "high", done=True, tags=["work"]),
        task(3, tags=["work"]), task(4, "high"),
    ])
    assert run(path, "list", "--all", "--tag", "work") == 0
    assert ids(capsys) == ["2", "3", "1"]


def test_ac7_legacy_file_lists_and_done_adds_no_key(tmp_path, capsys):
    path = saved(tmp_path, [task(1), task(2)])
    assert run(path, "list") == 0
    assert capsys.readouterr().out == "[ ] 1 T1\n[ ] 2 T2\n"
    assert run(path, "done", "1") == 0
    assert store.load(path)[0] == {"id": 1, "title": "T1", "done": True}
    assert run(path, "add", "N", "--priority", "high") == 0
    assert store.load(path)[2]["priority"] == "high"


@pytest.mark.parametrize("bad", ["urgent", "HIGH", 3, None, ["high"]])
@pytest.mark.parametrize("args", [["list"], ["list", "--all"], ["list", "--overdue"], ["list", "--tag", "x"]])
def test_ac8_malformed_stored_priority_is_reported(tmp_path, capsys, monkeypatch, bad, args):
    monkeypatch.setenv("TASKLIST_TODAY", "2026-10-05")
    path = saved(tmp_path, [task(7, bad)])
    raw = path.read_bytes()

    status = run(path, *args)

    captured = capsys.readouterr()
    assert status == 2
    assert captured.out == ""
    assert captured.err == f"error: task 7 has an invalid priority: {bad!r}\n"
    assert path.read_bytes() == raw


def test_ac8_malformed_priority_on_a_done_task_is_reported_by_list_all(tmp_path, capsys):
    path = saved(tmp_path, [task(7, "urgent", done=True)])
    raw = path.read_bytes()

    assert run(path, "list", "--all") == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: task 7 has an invalid priority: 'urgent'\n"
    assert path.read_bytes() == raw


def test_ac8_bad_priority_on_a_done_task_is_ignored_by_overdue_and_tag(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("TASKLIST_TODAY", "2026-10-05")
    path = saved(tmp_path, [
        task(1, "urgent", done=True, due="2026-10-01", tags=["x"]),
        task(2, due="2026-10-01", tags=["x"]),
    ])
    for args in (["list", "--overdue"], ["list", "--tag", "x"]):
        assert run(path, *args) == 0
        captured = capsys.readouterr()
        assert (captured.out, captured.err) == ("[ ] 2 T2 (due 2026-10-01) #x\n", "")


def test_ac8_bad_priority_on_a_done_task_is_ignored_by_plain_list(tmp_path, capsys):
    path = saved(tmp_path, [task(1, "urgent", done=True), task(2)])
    assert run(path, "list") == 0
    assert capsys.readouterr().out == "[ ] 2 T2\n"
    store.save(path, [task(1, "urgent", done=True), task(2, "urgent")])
    assert run(path, "list") == 2
