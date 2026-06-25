"""Acceptance tests for the CLI (rmkb-testgen / python -m ...)."""

import csv
import subprocess
import sys
import xml.etree.ElementTree as ET


def cli(*args, **kwargs):
    """Run the package CLI as a subprocess and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "robotmk_bridge_testdatagenerator", *args],
        capture_output=True,
        text=True,
        **kwargs,
    )


# --- --list ---

def test_list_exits_zero():
    result = cli("--list")
    assert result.returncode == 0


def test_list_shows_all_handlers():
    result = cli("--list")
    for handler in ("junit", "gatling", "zaproxy", "locust"):
        assert handler in result.stdout


# --- generate all ---

def test_generate_all_default(tmp_path):
    result = cli("--output-dir", str(tmp_path))
    assert result.returncode == 0
    assert (tmp_path / "junit.xml").exists()
    assert (tmp_path / "gatling.log").exists()
    assert (tmp_path / "zaproxy.xml").exists()
    assert (tmp_path / "locust.csv").exists()


def test_generate_prints_summary(tmp_path):
    result = cli("--output-dir", str(tmp_path))
    assert "Generated" in result.stdout
    assert "junit" in result.stdout


# --- --status ---

def test_status_passed(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--status", "passed")
    assert result.returncode == 0
    root = ET.parse(tmp_path / "junit.xml").getroot()
    assert root.get("failures") == "0"


def test_status_failed(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--status", "failed")
    assert result.returncode == 0
    root = ET.parse(tmp_path / "junit.xml").getroot()
    failures = int(root.get("failures", 0))
    errors = int(root.get("errors", 0))
    assert failures + errors > 0


def test_status_mixed(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--status", "mixed")
    assert result.returncode == 0


# --- --handlers filter ---

def test_handlers_single(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--handlers", "junit")
    assert result.returncode == 0
    assert (tmp_path / "junit.xml").exists()
    assert not (tmp_path / "gatling.log").exists()
    assert not (tmp_path / "locust.csv").exists()


def test_handlers_multiple(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--handlers", "junit", "locust")
    assert result.returncode == 0
    assert (tmp_path / "junit.xml").exists()
    assert (tmp_path / "locust.csv").exists()
    assert not (tmp_path / "gatling.log").exists()


# --- --count ---

def test_count_global_applies_to_junit(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--handlers", "junit", "--count", "3")
    assert result.returncode == 0
    root = ET.parse(tmp_path / "junit.xml").getroot()
    assert len(root.findall("testcase")) == 3


def test_count_per_handler_junit(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--handlers", "junit", "-n", "junit=8")
    assert result.returncode == 0
    root = ET.parse(tmp_path / "junit.xml").getroot()
    assert len(root.findall("testcase")) == 8


def test_count_per_handler_locust(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--handlers", "locust", "-n", "locust=3")
    assert result.returncode == 0
    with open(tmp_path / "locust.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    # 3 endpoints + 1 Aggregated
    assert len(rows) == 4


# --- error cases ---

def test_invalid_handler_exits_nonzero(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--handlers", "no_such_handler")
    assert result.returncode != 0


def test_invalid_count_exits_nonzero(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--count", "not_a_number")
    assert result.returncode != 0


# --- --verbose ---

def test_verbose_shows_output_dir(tmp_path):
    result = cli("--output-dir", str(tmp_path), "--verbose")
    assert result.returncode == 0
    assert str(tmp_path) in result.stdout
