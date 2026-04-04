import json
import pytest
from pathlib import Path

from teamagent.repository.file_utils import atomic_write, append_jsonl, read_jsonl, ensure_dir


def test_atomic_write(tmp_path):
    p = tmp_path / "test.json"
    data = {"key": "value"}
    atomic_write(p, data)
    assert json.loads(p.read_text()) == data


def test_atomic_write_overwrite(tmp_path):
    p = tmp_path / "test.json"
    atomic_write(p, {"v": 1})
    atomic_write(p, {"v": 2})
    assert json.loads(p.read_text()) == {"v": 2}


def test_append_jsonl(tmp_path):
    p = tmp_path / "log.jsonl"
    append_jsonl(p, {"id": "a"})
    append_jsonl(p, {"id": "b"})
    lines = p.read_text().strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["id"] == "a"
    assert json.loads(lines[1])["id"] == "b"


def test_read_jsonl(tmp_path):
    p = tmp_path / "log.jsonl"
    p.write_text('{"id":"a"}\n{"id":"b"}\n')
    items = read_jsonl(p)
    assert len(items) == 2
    assert items[0]["id"] == "a"


def test_read_jsonl_empty(tmp_path):
    p = tmp_path / "log.jsonl"
    p.write_text("")
    assert read_jsonl(p) == []


def test_read_jsonl_not_exists(tmp_path):
    p = tmp_path / "nope.jsonl"
    assert read_jsonl(p) == []


def test_ensure_dir(tmp_path):
    d = tmp_path / "a" / "b" / "c"
    ensure_dir(d)
    assert d.is_dir()
