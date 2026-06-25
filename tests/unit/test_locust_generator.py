"""Unit tests for the Locust stats CSV generator."""

import csv
from pathlib import Path

from robotmk_bridge_testdatagenerator.handlers import locust_generator

EXPECTED_COLUMNS = [
    "Type", "Name", "Request Count", "Failure Count",
    "Median Response Time", "Average Response Time",
    "Min Response Time", "Max Response Time", "Average Content Size",
    "Requests/s", "Failures/s",
    "50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%",
    "99.9%", "99.99%", "99.999%", "100%",
]


def _rows(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def test_creates_file(tmp_path):
    out = tmp_path / "stats.csv"
    locust_generator.generate(out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_header_columns(tmp_path):
    out = tmp_path / "stats.csv"
    locust_generator.generate(out)
    rows = _rows(out)
    assert list(rows[0].keys()) == EXPECTED_COLUMNS


def test_endpoint_plus_aggregated_row_count(tmp_path):
    out = tmp_path / "stats.csv"
    locust_generator.generate(out, num_endpoints=4)
    rows = _rows(out)
    assert len(rows) == 5  # 4 endpoints + 1 Aggregated


def test_last_row_is_aggregated(tmp_path):
    out = tmp_path / "stats.csv"
    locust_generator.generate(out, num_endpoints=3)
    rows = _rows(out)
    assert rows[-1]["Name"] == "Aggregated"
    assert rows[-1]["Type"] == "None"


def test_passed_no_endpoint_failures(tmp_path):
    out = tmp_path / "stats.csv"
    locust_generator.generate(out, test_status="passed", num_endpoints=6)
    endpoint_rows = [r for r in _rows(out) if r["Name"] != "Aggregated"]
    assert all(int(r["Failure Count"]) == 0 for r in endpoint_rows)


def test_failed_all_endpoints_have_failures(tmp_path):
    out = tmp_path / "stats.csv"
    locust_generator.generate(out, test_status="failed", num_endpoints=5)
    endpoint_rows = [r for r in _rows(out) if r["Name"] != "Aggregated"]
    assert all(int(r["Failure Count"]) > 0 for r in endpoint_rows)


def test_mixed_partial_failures(tmp_path):
    out = tmp_path / "stats.csv"
    locust_generator.generate(out, test_status="mixed", num_endpoints=6)
    endpoint_rows = [r for r in _rows(out) if r["Name"] != "Aggregated"]
    failure_counts = [int(r["Failure Count"]) for r in endpoint_rows]
    # indices 1, 4 get failures; 0, 2, 3, 5 don't
    assert any(f > 0 for f in failure_counts)
    assert any(f == 0 for f in failure_counts)


def test_aggregated_request_count_is_sum(tmp_path):
    out = tmp_path / "stats.csv"
    locust_generator.generate(out, num_endpoints=4)
    rows = _rows(out)
    endpoint_rows = [r for r in rows if r["Name"] != "Aggregated"]
    aggregated = next(r for r in rows if r["Name"] == "Aggregated")
    total = sum(int(r["Request Count"]) for r in endpoint_rows)
    assert int(aggregated["Request Count"]) == total


def test_percentile_columns_are_numeric(tmp_path):
    out = tmp_path / "stats.csv"
    locust_generator.generate(out, num_endpoints=3)
    for row in _rows(out):
        for col in ["50%", "95%", "99%", "100%"]:
            assert int(row[col]) >= 0
