"""Tests for tasklist.store: loading, atomic saving and choosing the file."""

import json
from pathlib import Path

import pytest

from tasklist import store

TASKS = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Call Sam", "done": True},
]


def test_load_missing_file_returns_empty_list(tmp_path):
    assert store.load(tmp_path / "tasks.json") == []


def test_save_writes_indented_json_with_sorted_keys(tmp_path):
    path = tmp_path / "tasks.json"

    store.save(path, [{"title": "Buy milk", "id": 1, "done": False}])

    assert path.read_text(encoding="utf-8") == (
        "[\n"
        "  {\n"
        '    "done": false,\n'
        '    "id": 1,\n'
        '    "title": "Buy milk"\n'
        "  }\n"
        "]\n"
    )
    assert store.load(path) == [{"id": 1, "title": "Buy milk", "done": False}]


def test_failed_save_keeps_the_old_file_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "tasks.json"
    store.save(path, TASKS)
    unwritable = [{"id": 3, "title": object(), "done": False}]  # fails midway

    with pytest.raises(TypeError):
        store.save(path, unwritable)

    assert json.loads(path.read_text(encoding="utf-8")) == TASKS
    assert list(tmp_path.iterdir()) == [path]


def test_resolve_path_order_is_argument_then_environment_then_default(monkeypatch):
    monkeypatch.delenv("TASKLIST_FILE", raising=False)
    assert store.resolve_path() == Path("tasks.json")

    monkeypatch.setenv("TASKLIST_FILE", "from_env.json")
    assert store.resolve_path() == Path("from_env.json")
    assert store.resolve_path("from_arg.json") == Path("from_arg.json")
