"""Unit tests for the OWASP ZAP XML generator."""

import xml.etree.ElementTree as ET
from pathlib import Path

from robotmk_bridge_testdatagenerator.handlers import zap_generator
from robotmk_bridge_testdatagenerator.handlers.zap_generator import (
    get_high_risk_alerts,
    get_low_risk_alerts,
    get_mixed_risk_alerts,
)


def _root(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def _risk_codes(path: Path) -> list:
    return [int(a.findtext("riskcode", "0")) for a in _root(path).iter("alertitem")]


# --- Structure ---

def test_creates_file(tmp_path):
    out = tmp_path / "report.xml"
    zap_generator.generate(out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_valid_xml_root(tmp_path):
    out = tmp_path / "report.xml"
    zap_generator.generate(out)
    root = _root(out)
    assert root.tag == "OWASPZAPReport"
    assert root.get("version") == "2.7.0"


def test_site_count(tmp_path):
    out = tmp_path / "report.xml"
    zap_generator.generate(out, num_sites=2)
    assert len(_root(out).findall("site")) == 2


def test_each_site_has_alerts(tmp_path):
    out = tmp_path / "report.xml"
    zap_generator.generate(out, num_sites=3)
    for site in _root(out).findall("site"):
        assert site.find("alerts") is not None
        assert len(site.find("alerts").findall("alertitem")) >= 1


# --- Status semantics ---

def test_passed_only_low_risk(tmp_path):
    out = tmp_path / "report.xml"
    zap_generator.generate(out, test_status="passed", num_sites=3)
    assert all(c <= 1 for c in _risk_codes(out))


def test_failed_only_high_risk(tmp_path):
    out = tmp_path / "report.xml"
    zap_generator.generate(out, test_status="failed", num_sites=3)
    # High-risk pool contains only riskcode 2 and 3
    assert all(c >= 2 for c in _risk_codes(out))


# --- Helper function unit tests (deterministic) ---

def test_low_risk_pool_riskcode(tmp_path):
    alerts = get_low_risk_alerts()
    assert all(int(a["riskcode"]) <= 1 for a in alerts)


def test_high_risk_pool_riskcode(tmp_path):
    alerts = get_high_risk_alerts()
    assert all(int(a["riskcode"]) >= 2 for a in alerts)


def test_mixed_pool_contains_varied_levels(tmp_path):
    alerts = get_mixed_risk_alerts()
    levels = {int(a["riskcode"]) for a in alerts}
    assert len(levels) > 1, "mixed pool must span more than one risk level"
