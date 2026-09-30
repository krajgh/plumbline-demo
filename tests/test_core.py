"""Tests for tasklist.core: adding, completing and filtering tasks."""

import datetime

import pytest

from tasklist import core


def test_add_task_numbers_from_one_then_highest_id_plus_one():
    tasks = []

    first = core.add_task(tasks, "  Buy milk ")
    assert first == {"id": 1, "title": "Buy milk", "done": False}
    assert tasks == [first]

    tasks.append({"id": 7, "title": "Call Sam", "done": True})  # ids may have gaps
    assert core.add_task(tasks, "Pay rent")["id"] == 8


@pytest.mark.parametrize("title", ["", "   "])
def test_add_task_rejects_a_blank_title(title):
    tasks = []

    with pytest.raises(ValueError):
        core.add_task(tasks, title)

    assert tasks == []


def test_complete_task_marks_only_that_task_done():
    tasks = [
        {"id": 1, "title": "Buy milk", "done": False},
        {"id": 2, "title": "Call Sam", "done": False},
    ]

    done = core.complete_task(tasks, 2)

    assert done == {"id": 2, "title": "Call Sam", "done": True}
    assert [task["done"] for task in tasks] == [False, True]


def test_complete_task_unknown_id_raises_key_error():
    tasks = [{"id": 1, "title": "Buy milk", "done": False}]

    with pytest.raises(KeyError):
        core.complete_task(tasks, 99)

    assert tasks == [{"id": 1, "title": "Buy milk", "done": False}]


def test_visible_tasks_hides_done_tasks_unless_show_all():
    tasks = [
        {"id": 2, "title": "Call Sam", "done": True},
        {"id": 3, "title": "Pay rent", "done": False},
        {"id": 1, "title": "Buy milk", "done": False},
    ]

    open_only = core.visible_tasks(tasks)
    everything = core.visible_tasks(tasks, show_all=True)

    assert [task["id"] for task in open_only] == [1, 3]
    assert [task["id"] for task in everything] == [1, 2, 3]


# --- due dates ---


def test_ac1_add_task_with_due_sets_the_due_key_only_when_given():
    tasks = []

    dated = core.add_task(tasks, "Pay rent", due="2026-10-01")
    plain = core.add_task(tasks, "Buy milk")

    assert dated == {"id": 1, "title": "Pay rent", "done": False, "due": "2026-10-01"}
    assert "due" not in plain


@pytest.mark.parametrize(
    "due", ["2026-02-30", "tomorrow", "2026-2-3", "20261001", "2026-13-01", ""]
)
def test_ac2_add_task_rejects_a_bad_due_and_leaves_tasks_alone(due):
    tasks = []
    raised = False

    try:
        core.add_task(tasks, "X", due=due)
    except ValueError:
        raised = True

    assert raised
    assert tasks == []


def test_ac2_parse_date_is_strict_and_accepts_a_leap_day():
    assert core.parse_date("2028-02-29") == datetime.date(2028, 2, 29)
    for bad in ["2026-02-30", "20261001", "2026-2-3", "", "tomorrow"]:
        try:
            core.parse_date(bad)
            raised = False
        except ValueError:
            raised = True
        assert raised, bad


def test_ac4_ac5_overdue_tasks_filters_and_orders_by_explicit_today():
    def t(id, due=None, done=False):
        task = {"id": id, "title": f"t{id}", "done": done}
        if due:
            task["due"] = due
        return task

    tasks = [
        t(1, "2026-09-30"), t(7, "2026-09-01"), t(3, "2026-10-01"),
        t(4, "2026-12-01"), t(5), t(6, "2026-08-01", done=True), t(2, "2026-09-01"),
    ]

    ids = lambda today: [x["id"] for x in core.overdue_tasks(tasks, today)]
    assert ids(datetime.date(2026, 10, 1)) == [2, 7, 1]
    assert ids(datetime.date(2026, 1, 1)) == []
    assert ids(datetime.date(2026, 10, 2)) == [2, 7, 1, 3]
