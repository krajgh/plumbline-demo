"""Tests for tags: add --tag, tag, untag, list --tag and the tag display."""

import pytest

from tasklist import store
from tasklist.cli import main

TASKS = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Call Sam", "done": True},
]


@pytest.fixture
def tasks_file(tmp_path):
    path = tmp_path / "tasks.json"
    store.save(path, TASKS)
    return path


def run(path, *args):
    return main(["--file", str(path), *args])


def stored_tasks(tmp_path, tasks):
    path = tmp_path / "tagged.json"
    store.save(path, tasks)
    return path


def assert_error(path, capsys, before, status, err):
    captured = capsys.readouterr()
    assert status == 2
    assert captured.out == ""
    assert captured.err == err
    assert store.load(path) == before


def test_ac1_add_stores_tags_in_order_without_duplicates(tmp_path, capsys):
    path = tmp_path / "tasks.json"

    assert run(path, "add", "Pay rent", "--tag", "work", "--tag", "home", "--tag", "work") == 0
    assert capsys.readouterr().out == "added 1\n"
    assert run(path, "add", "Plain") == 0
    assert run(path, "add", "Quarter", "--tag", "2026-q4") == 0

    assert store.load(path) == [
        {"id": 1, "title": "Pay rent", "done": False, "tags": ["work", "home"]},
        {"id": 2, "title": "Plain", "done": False},
        {"id": 3, "title": "Quarter", "done": False, "tags": ["2026-q4"]},
    ]


def test_ac1_core_add_task_dedupes_tags_and_omits_empty():
    from tasklist import core

    tasks = []
    assert core.add_task(tasks, "A", tags=["b", "a", "b"])["tags"] == ["b", "a"]
    assert "tags" not in core.add_task(tasks, "B")
    assert "tags" not in core.add_task(tasks, "C", tags=[])
    with pytest.raises(ValueError):
        core.add_task(tasks, "D", tags=["ok", "BAD"])
    assert len(tasks) == 3


@pytest.mark.parametrize(
    "name,ok",
    [("work", True), ("a-1", True), ("-", True), ("", False), ("Work", False),
     ("a b", False), ("a_b", False), ("é", False), ("work\n", False), ("٣", False)],
)
def test_ac1_is_valid_tag(name, ok):
    from tasklist.core import is_valid_tag

    assert is_valid_tag(name) is ok


@pytest.mark.parametrize(
    "tags,bad",
    [(["Work"], "Work"), (["a b"], "a b"), (["a_b"], "a_b"), (["é"], "é"), (["ok", "BAD"], "BAD"),
     (["Bad1", "Bad2"], "Bad1")],
)
def test_ac2_add_with_an_invalid_tag_is_refused(tasks_file, capsys, tags, bad):
    status = run(tasks_file, "add", "X", *[a for t in tags for a in ("--tag", t)])

    assert_error(tasks_file, capsys, TASKS, status, f"error: invalid tag: {bad}\n")


def test_ac2_invalid_tag_does_not_create_the_file(tmp_path, capsys):
    path = tmp_path / "new.json"

    assert run(path, "add", "X", "--tag", "Work") == 2

    assert capsys.readouterr().err == "error: invalid tag: Work\n"
    assert not path.exists()


def test_ac3_tag_appends_and_retagging_is_a_no_op(tasks_file, capsys):
    for tag, expected in [("work", ["work"]), ("home", ["work", "home"]), ("work", ["work", "home"])]:
        assert run(tasks_file, "tag", "1", tag) == 0
        assert store.load(tasks_file)[0]["tags"] == expected

    assert capsys.readouterr().out == "tagged 1\n" * 3


@pytest.mark.parametrize(
    "args,err",
    [(["tag", "1", "Bad"], "invalid tag: Bad"),
     (["tag", "99", "work"], "no task with id 99"),
     (["tag", "99", "Bad"], "invalid tag: Bad"),
     (["untag", "99", "work"], "no task with id 99")],
)
def test_ac3_ac4_refused_tag_commands_leave_the_file_unchanged(tasks_file, capsys, args, err):
    status = run(tasks_file, *args)

    assert_error(tasks_file, capsys, TASKS, status, f"error: {err}\n")


def test_ac3_ac4_core_tag_errors():
    from tasklist import core

    tasks = [{"id": 1, "title": "A", "done": False, "tags": ["x"]}]
    with pytest.raises(ValueError):
        core.add_tag(tasks, 99, "Bad")
    with pytest.raises(KeyError):
        core.add_tag(tasks, 99, "ok")
    assert core.add_tag(tasks, 1, "ok")["tags"] == ["x", "ok"]
    with pytest.raises(KeyError):
        core.remove_tag(tasks, 99, "x")
    with pytest.raises(ValueError):
        core.remove_tag(tasks, 1, "y")
    core.remove_tag(tasks, 1, "ok")
    assert "tags" not in core.remove_tag(tasks, 1, "x")


def test_ac4_untag_removes_one_then_deletes_the_key_when_empty(tmp_path, capsys):
    path = stored_tasks(tmp_path, [{"id": 1, "title": "A", "done": False, "tags": ["work", "home"]}])

    assert run(path, "untag", "1", "work") == 0
    assert capsys.readouterr().out == "untagged 1\n"
    assert store.load(path)[0]["tags"] == ["home"]

    assert run(path, "untag", "1", "home") == 0
    assert "tags" not in store.load(path)[0]


def test_ac4_untag_a_tag_the_task_lacks_is_refused(tmp_path, capsys):
    before = [
        {"id": 1, "title": "A", "done": False, "tags": ["home"]},
        {"id": 2, "title": "B", "done": False},
    ]
    path = stored_tasks(tmp_path, before)

    for task_id in "12":
        status = run(path, "untag", task_id, "work")
        assert_error(path, capsys, before, status, f"error: task {task_id} does not have tag work\n")


def test_ac5_list_shows_tags_after_the_due_date(tmp_path, capsys):
    path = stored_tasks(tmp_path, [
        {"id": 1, "title": "Buy milk", "done": False, "tags": ["work", "home"]},
        {"id": 2, "title": "Pay", "done": False, "due": "2026-10-01", "tags": ["work"]},
        {"id": 3, "title": "Plain", "done": False},
        {"id": 4, "title": "Empty", "done": False, "tags": []},
    ])

    assert run(path, "list") == 0

    assert capsys.readouterr().out == (
        "[ ] 1 Buy milk #work #home\n"
        "[ ] 2 Pay (due 2026-10-01) #work\n"
        "[ ] 3 Plain\n"
        "[ ] 4 Empty\n"
    )


MIXED = [
    {"id": 1, "title": "One", "done": False, "tags": ["work"]},
    {"id": 2, "title": "Two", "done": True, "tags": ["work"]},
    {"id": 3, "title": "Three", "done": False, "tags": ["home"]},
    {"id": 4, "title": "Four", "done": False},
    {"id": 5, "title": "Five", "done": False, "due": "2026-01-01", "tags": ["work"]},
]


@pytest.mark.parametrize(
    "args,ids",
    [(["--tag", "work"], ["1", "5"]),
     (["--all", "--tag", "work"], ["1", "2", "5"]),
     (["--overdue", "--tag", "work"], ["5"]),
     (["--tag", "nosuch"], []),
     (["--tag", "wor"], [])],
)
def test_ac6_list_tag_filters_and_combines_with_other_flags(tmp_path, capsys, monkeypatch, args, ids):
    monkeypatch.setenv("TASKLIST_TODAY", "2026-10-05")
    path = stored_tasks(tmp_path, MIXED)

    assert run(path, "list", *args) == 0

    assert [line[4:].split()[0] for line in capsys.readouterr().out.splitlines()] == ids


def test_ac7_done_keeps_the_tags(tmp_path):
    path = stored_tasks(tmp_path, [{"id": 1, "title": "A", "done": False}])

    assert run(path, "tag", "1", "work") == 0
    assert run(path, "done", "1") == 0

    assert store.load(path) == [{"id": 1, "title": "A", "done": True, "tags": ["work"]}]


def test_ac8_empty_tag_is_refused_with_the_exact_message(tasks_file, capsys):
    status = run(tasks_file, "add", "Title", "--tag", "")

    assert_error(tasks_file, capsys, TASKS, status, "error: invalid tag: \n")


# --- dash-leading tags use the standard argparse forms ---


def test_ac1_ac3_ac4_ac6_dash_leading_tags_use_the_argparse_forms(tmp_path, capsys):
    path = tmp_path / "tasks.json"

    assert run(path, "add", "T", "--tag=-x", "--tag=-") == 0
    assert run(path, "add", "U", "--tag=x") == 0
    assert store.load(path)[0]["tags"] == ["-x", "-"]
    assert run(path, "untag", "1", "--", "-") == 0
    assert run(path, "list", "--tag=-x") == 0
    assert capsys.readouterr().out == "added 1\nadded 2\nuntagged 1\n[ ] 1 T #-x\n"
    assert run(path, "untag", "1", "--", "-x") == 0
    assert run(path, "tag", "1", "--", "-x") == 0
    assert store.load(path)[0]["tags"] == ["-x"]


@pytest.mark.parametrize("command", ["tag", "untag"])
def test_ac3_ac4_help_prints_usage_and_exits_zero(tasks_file, capsys, command):
    with pytest.raises(SystemExit) as info:
        run(tasks_file, command, "--help")

    assert info.value.code == 0
    assert "usage:" in capsys.readouterr().out


# --- a stored "tags" value that is not a list of strings ---

BAD_TAGS = ["ab", None, ["ok", 3], 5]


@pytest.mark.parametrize("bad", BAD_TAGS)
@pytest.mark.parametrize(
    "args",
    [["tag", "7", "x"], ["untag", "7", "x"], ["list"], ["list", "--all"], ["list", "--overdue"],
     ["list", "--tag", "x"]],
)
def test_ac6_malformed_stored_tags_name_the_task_by_id(tmp_path, capsys, monkeypatch, bad, args):
    monkeypatch.setenv("TASKLIST_TODAY", "2026-10-05")
    before = [{"id": 7, "title": "A", "done": False, "tags": bad}]
    path = stored_tasks(tmp_path, before)

    try:
        status = run(path, *args)
    except Exception as exc:
        pytest.fail(f"main() raised {exc!r}")

    assert_error(path, capsys, before, status, f"error: task 7 has invalid tags: {bad!r}\n")


def test_ac6_bad_tags_of_other_or_hidden_tasks_are_ignored(tmp_path, capsys):
    before = [
        {"id": 1, "title": "A", "done": False, "tags": ["x"]},
        {"id": 2, "title": "B", "done": True, "tags": 5},
    ]
    path = stored_tasks(tmp_path, before)

    assert run(path, "tag", "1", "y") == 0
    assert run(path, "untag", "1", "y") == 0
    assert run(path, "list", "--tag", "x") == 0  # hidden done task 2 is not checked
    assert capsys.readouterr().out == "tagged 1\nuntagged 1\n[ ] 1 A #x\n"
    assert run(path, "tag", "2", "Bad") == 2  # the invalid NAME wins over the stored tags
    assert capsys.readouterr().err == "error: invalid tag: Bad\n"
