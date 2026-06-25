"""Unit tests for the Gatling simulation log generator."""

from pathlib import Path

from robotmk_bridge_testdatagenerator.handlers import gatling_generator


def _records(path: Path) -> dict:
    """Parse a simulation.log into record-type buckets."""
    buckets: dict = {"RUN": [], "USER": [], "REQUEST": []}
    for line in path.read_text().splitlines():
        parts = line.split("\t")
        rtype = parts[0] if parts else ""
        if rtype in buckets:
            buckets[rtype].append(parts)
    return buckets


def test_creates_file(tmp_path):
    out = tmp_path / "simulation.log"
    gatling_generator.generate(out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_exactly_one_run_record(tmp_path):
    out = tmp_path / "simulation.log"
    gatling_generator.generate(out)
    assert len(_records(out)["RUN"]) == 1


def test_run_record_version(tmp_path):
    out = tmp_path / "simulation.log"
    gatling_generator.generate(out)
    run = _records(out)["RUN"][0]
    assert run[-1] == "2.0"


def test_request_count(tmp_path):
    out = tmp_path / "simulation.log"
    gatling_generator.generate(out, num_requests=7)
    assert len(_records(out)["REQUEST"]) == 7


def test_user_records_bookend_requests(tmp_path):
    out = tmp_path / "simulation.log"
    gatling_generator.generate(out, num_requests=6)
    rec = _records(out)
    starts = [r for r in rec["USER"] if r[3] == "START"]
    ends = [r for r in rec["USER"] if r[3] == "END"]
    assert len(starts) == len(ends)
    assert len(starts) >= 1


def test_passed_all_ok(tmp_path):
    out = tmp_path / "simulation.log"
    gatling_generator.generate(out, test_status="passed", num_requests=10)
    statuses = [r[7] for r in _records(out)["REQUEST"] if len(r) > 7]
    assert all(s == "OK" for s in statuses)


def test_failed_all_ko(tmp_path):
    out = tmp_path / "simulation.log"
    gatling_generator.generate(out, test_status="failed", num_requests=10)
    statuses = [r[7] for r in _records(out)["REQUEST"] if len(r) > 7]
    assert all(s == "KO" for s in statuses)


def test_mixed_has_both_ok_and_ko(tmp_path):
    out = tmp_path / "simulation.log"
    gatling_generator.generate(out, test_status="mixed", num_requests=12)
    statuses = [r[7] for r in _records(out)["REQUEST"] if len(r) > 7]
    assert "OK" in statuses
    assert "KO" in statuses
