"""Acceptance tests for the public library API."""

import xml.etree.ElementTree as ET

import pytest

from robotmk_bridge_testdatagenerator import (
    generate_all_handler_files,
    generate_handler_file,
    get_supported_handlers,
)


def test_get_supported_handlers_returns_all_four():
    handlers = get_supported_handlers()
    assert set(handlers) == {"junit", "gatling", "zaproxy", "locust"}


def test_generate_all_returns_path_dict(tmp_path):
    files = generate_all_handler_files(tmp_path)
    assert isinstance(files, dict)
    assert set(files.keys()) == {"junit", "gatling", "zaproxy", "locust"}


def test_generate_all_files_exist(tmp_path):
    files = generate_all_handler_files(tmp_path)
    for path in files.values():
        assert path.exists()
        assert path.stat().st_size > 0


def test_generate_all_creates_nested_dir(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    generate_all_handler_files(nested)
    assert nested.is_dir()


def test_generate_all_correct_extensions(tmp_path):
    files = generate_all_handler_files(tmp_path)
    assert files["junit"].suffix == ".xml"
    assert files["gatling"].suffix == ".log"
    assert files["zaproxy"].suffix == ".xml"
    assert files["locust"].suffix == ".csv"


def test_generate_all_with_handler_kwargs(tmp_path):
    files = generate_all_handler_files(
        tmp_path,
        handler_kwargs={"junit": {"num_tests": 7}},
    )
    root = ET.parse(files["junit"]).getroot()
    assert len(root.findall("testcase")) == 7


def test_generate_all_status_passed(tmp_path):
    files = generate_all_handler_files(tmp_path, test_status="passed")
    root = ET.parse(files["junit"]).getroot()
    assert root.get("failures") == "0"


def test_generate_all_status_failed(tmp_path):
    files = generate_all_handler_files(tmp_path, test_status="failed")
    root = ET.parse(files["junit"]).getroot()
    failures = int(root.get("failures", 0))
    errors = int(root.get("errors", 0))
    assert failures + errors > 0


def test_generate_single_handler_returns_path(tmp_path):
    out = tmp_path / "out.xml"
    returned = generate_handler_file("junit", out)
    assert returned == out
    assert out.exists()


def test_generate_single_handler_invalid_raises(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        generate_handler_file("no_such_handler", tmp_path / "x.txt")


def test_generate_all_locust_kwargs(tmp_path):
    import csv
    files = generate_all_handler_files(
        tmp_path,
        handler_kwargs={"locust": {"num_endpoints": 3}},
    )
    with open(files["locust"], newline="") as f:
        rows = list(csv.DictReader(f))
    # 3 endpoints + 1 Aggregated
    assert len(rows) == 4
