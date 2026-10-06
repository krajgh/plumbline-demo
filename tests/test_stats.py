"""Tests for the stats command."""

import json

import pytest

from tasklist.cli import main

SIX_ZERO = "open: 0\ndone: 0\nhigh: 0\nnormal: 0\nlow: 0\noverdue: 0\n"


def six(o, d, h, n, l, v):
    return f"open: {o}\ndone: {d}\nhigh: {h}\nnormal: {n}\nlow: {l}\noverdue: {v}\n"


@pytest.fixture(autouse=True)
def today(monkeypatch):
    monkeypatch.setenv("TASKLIST_TODAY", "2026-10-06")


def write(tmp_path, tasks):
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps(tasks))
    return path


def stats(path, capsys, *extra):
    status = main(["--file", str(path), "stats", *extra])
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def t(id, done=False, **fields):
    return {"id": id, "title": f"t{id}", "done": done, **fields}


def test_ac1_stats_prints_six_counts(tmp_path, capsys):
    path = write(tmp_path, [
        t(1, due="2026-10-01", priority="high"),
        t(2),
        t(3, priority="low"),
        t(4, True, priority="high"),
    ])
    assert stats(path, capsys) == (0, six(3, 1, 1, 1, 1, 1), "")


def test_ac1_overdue_matches_list_overdue(tmp_path, capsys):
    path = write(tmp_path, [
        t(1, due="2026-10-01"), t(2, due="2026-10-06"), t(3, due="2020-01-01"),
        t(4, True, due="2020-01-01"), t(5),
    ])
    main(["--file", str(path), "list", "--overdue"])
    listed = len(capsys.readouterr().out.splitlines())
    _, out, _ = stats(path, capsys)
    assert out.splitlines()[5] == f"overdue: {listed}"
    assert listed == 2


def test_ac2_due_today_and_done_not_overdue(tmp_path, capsys):
    path = write(tmp_path, [
        t(1, due="2026-10-05"), t(2, due="2026-10-06"), t(3, due="2026-10-07"),
        t(4, True, due="2026-10-01"),
    ])
    assert stats(path, capsys) == (0, six(3, 1, 0, 3, 0, 1), "")


def test_ac2_invalid_today_is_an_error(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("TASKLIST_TODAY", "garbage")
    path = write(tmp_path, [t(1)])
    assert stats(path, capsys) == (2, "", "error: invalid TASKLIST_TODAY: garbage\n")


def test_ac3_per_tag_lines_ordered(tmp_path, capsys):
    path = write(tmp_path, [
        t(1, tags=["b", "a"]), t(2, tags=["b"]), t(3, tags=["c"]), t(4, True, tags=["z"]),
    ])
    assert stats(path, capsys) == (
        0, six(3, 1, 0, 3, 0, 0) + "#b: 2\n#a: 1\n#c: 1\n", "")


def test_ac3_no_tags_means_six_lines(tmp_path, capsys):
    path = write(tmp_path, [t(1), t(2, True, tags=["z"])])
    status, out, _ = stats(path, capsys)
    assert status == 0
    assert out == six(1, 1, 0, 1, 0, 0)


WORK_TASKS = [
    t(1, tags=["work"], priority="high", due="2026-10-01"),
    t(2, tags=["work"]),
    t(3, True, tags=["work"]),
    t(4, tags=["home"], priority="high"),
    t(5),
]


def test_ac4_tag_limits_every_figure(tmp_path, capsys):
    path = write(tmp_path, WORK_TASKS)
    assert stats(path, capsys, "--tag", "work") == (0, six(2, 1, 1, 1, 0, 1), "")


def test_ac4_unknown_tag_gives_zeros(tmp_path, capsys):
    path = write(tmp_path, WORK_TASKS)
    assert stats(path, capsys, "--tag", "nosuch") == (0, SIX_ZERO, "")


def test_ac5_missing_and_empty_file(tmp_path, capsys):
    missing = tmp_path / "missing.json"
    assert stats(missing, capsys) == (0, SIX_ZERO, "")
    assert not missing.exists()
    assert stats(write(tmp_path, []), capsys) == (0, SIX_ZERO, "")


@pytest.mark.parametrize("field", [
    {"due": "2026-13-45"}, {"due": 5}, {"tags": "x"}, {"tags": [1]},
    {"priority": "urgent"}, {"priority": 5},
])
def test_ac6_bad_open_task_value_is_an_error(tmp_path, capsys, field):
    path = write(tmp_path, [t(1), t(3, **field)])
    status, out, err = stats(path, capsys)
    assert status == 2
    assert out == ""
    assert err.startswith("error: task 3 ") and err.count("\n") == 1


def test_ac6_done_task_checks(tmp_path, capsys):
    path = write(tmp_path, [t(1), t(2, True, tags="x")])
    assert stats(path, capsys)[0] == 0
    status, out, err = stats(path, capsys, "--tag", "x")
    assert (status, out) == (2, "")
    assert err.startswith("error: task 2 ") and err.count("\n") == 1
    path = write(tmp_path, [t(1), t(2, True, due="bad", priority="urgent")])
    assert stats(path, capsys)[0] == 0


def test_ac6_due_checked_before_priority(tmp_path, capsys):
    path = write(tmp_path, [t(1, priority="urgent"), t(2, due="2026-13-45")])
    status, out, err = stats(path, capsys)
    assert (status, out) == (2, "")
    assert err.startswith("error: task 2 ")


def test_ac7_legacy_tasks(tmp_path, capsys):
    path = write(tmp_path, [
        {"id": 1, "title": "a", "done": False}, {"id": 2, "title": "b", "done": True},
    ])
    assert stats(path, capsys) == (0, six(1, 1, 0, 1, 0, 0), "")


@pytest.mark.parametrize("field, message", [
    ({"due": "2026-13-45"}, "task 3 has an invalid due date: 2026-13-45"),
    ({"due": 5}, "task 3 has an invalid due date: 5"),
    ({"tags": "x"}, "task 3 has invalid tags: 'x'"),
    ({"tags": [1]}, "task 3 has invalid tags: [1]"),
    ({"priority": "urgent"}, "task 3 has an invalid priority: 'urgent'"),
    ({"priority": 5}, "task 3 has an invalid priority: 5"),
])
def test_ac6_error_message_is_exact(tmp_path, capsys, field, message):
    path = write(tmp_path, [t(1), t(3, **field)])
    assert stats(path, capsys) == (2, "", f"error: {message}\n")


def test_ac6_tags_checked_after_due_before_priority(tmp_path, capsys):
    path = write(tmp_path, [t(1, tags="x"), t(2, due="bad")])
    assert stats(path, capsys)[2].startswith("error: task 2 has an invalid due date")
    path = write(tmp_path, [t(1, priority="urgent"), t(2, tags="x")])
    assert stats(path, capsys)[2].startswith("error: task 2 has invalid tags")


@pytest.mark.parametrize("field", [{"due": "bad"}, {"priority": "urgent"}])
def test_ac6_tag_filter_still_checks_untagged_open_tasks(tmp_path, capsys, field):
    path = write(tmp_path, [t(1, tags=["work"]), t(2, **field)])
    status, out, err = stats(path, capsys, "--tag", "work")
    assert (status, out) == (2, "")
    assert err.startswith("error: task 2 ")


def test_ac3_duplicate_tag_counts_once(tmp_path, capsys):
    path = write(tmp_path, [t(1, tags=["a", "a"])])
    assert stats(path, capsys) == (0, six(1, 0, 0, 1, 0, 0) + "#a: 1\n", "")
    assert stats(path, capsys, "--tag", "a") == (0, six(1, 0, 0, 1, 0, 0), "")


def test_ac2_empty_today_uses_clock(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("TASKLIST_TODAY", "")
    path = write(tmp_path, [t(1, due="2000-01-01"), t(2, due="2999-01-01")])
    assert stats(path, capsys) == (0, six(2, 0, 0, 2, 0, 1), "")


def test_ac8_stats_does_not_write_file(tmp_path, capsys):
    path = write(tmp_path, WORK_TASKS)
    before = path.read_bytes()
    assert stats(path, capsys)[0] == 0
    assert stats(path, capsys, "--tag", "work")[0] == 0
    assert path.read_bytes() == before
