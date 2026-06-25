"""Unit tests for the JUnit XML generator."""

import xml.etree.ElementTree as ET
from pathlib import Path

from robotmk_bridge_testdatagenerator.handlers import junit_generator


def _root(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def test_creates_file(tmp_path):
    out = tmp_path / "result.xml"
    junit_generator.generate(out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_valid_xml_structure(tmp_path):
    out = tmp_path / "result.xml"
    junit_generator.generate(out)
    root = _root(out)
    assert root.tag == "testsuite"
    assert root.get("name") == "RobotmkBridgeTests"


def test_default_count(tmp_path):
    out = tmp_path / "result.xml"
    junit_generator.generate(out)
    assert len(_root(out).findall("testcase")) == 5


def test_custom_count(tmp_path):
    out = tmp_path / "result.xml"
    junit_generator.generate(out, num_tests=12)
    root = _root(out)
    assert len(root.findall("testcase")) == 12
    assert root.get("tests") == "12"


def test_passed_no_failures(tmp_path):
    out = tmp_path / "result.xml"
    junit_generator.generate(out, test_status="passed", num_tests=10)
    root = _root(out)
    assert root.get("failures") == "0"
    assert root.get("errors") == "0"
    assert root.find(".//failure") is None
    assert root.find(".//error") is None


def test_failed_all_fail(tmp_path):
    out = tmp_path / "result.xml"
    junit_generator.generate(out, test_status="failed", num_tests=10)
    root = _root(out)
    failures = int(root.get("failures", 0))
    errors = int(root.get("errors", 0))
    assert failures + errors == 10


def test_mixed_partial_failures(tmp_path):
    out = tmp_path / "result.xml"
    junit_generator.generate(out, test_status="mixed", num_tests=9)
    root = _root(out)
    failures = int(root.get("failures", 0))
    errors = int(root.get("errors", 0))
    # indices 0, 3, 6 fail → 3 out of 9
    assert failures + errors == 3


def test_testsuite_counts_match_content(tmp_path):
    out = tmp_path / "result.xml"
    junit_generator.generate(out, test_status="mixed", num_tests=9)
    root = _root(out)
    reported_failures = int(root.get("failures", 0))
    reported_errors = int(root.get("errors", 0))
    actual_failures = len(root.findall(".//failure"))
    actual_errors = len(root.findall(".//error"))
    assert reported_failures == actual_failures
    assert reported_errors == actual_errors
