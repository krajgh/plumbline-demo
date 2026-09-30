"""Tests for tasklist.core: adding, completing and filtering tasks."""

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
