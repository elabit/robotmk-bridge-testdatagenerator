"""Locust stats CSV test data generator."""

import random
from pathlib import Path
from typing import Dict, List

# Example output (*_stats.csv):
# "Type","Name","Request Count","Failure Count","Median Response Time","Average Response Time","Min Response Time","Max Response Time","Average Content Size","Requests/s","Failures/s","50%","66%","75%","80%","90%","95%","98%","99%","99.9%","99.99%","99.999%","100%"
# "GET","/",10,0,72,75,66,89,2175,0.26,0.00,73,75,86,87,89,89,89,89,89,89,89,89
# "POST","/",5,5,300,323,288,402,157,0.13,0.13,300,330,330,400,400,400,400,400,400,400,400,400
# "GET","/item",24,0,80,79,67,100,2175,0.63,0.00,81,85,86,86,89,92,100,100,100,100,100,100
# "None","Aggregated",39,5,81,109,66,402,1916,1.03,0.13,81,86,87,89,300,330,400,400,400,400,400,400

HEADER = [
    "Type", "Name", "Request Count", "Failure Count",
    "Median Response Time", "Average Response Time",
    "Min Response Time", "Max Response Time", "Average Content Size",
    "Requests/s", "Failures/s",
    "50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%",
    "99.9%", "99.99%", "99.999%", "100%",
]

ENDPOINT_POOL = [
    ("GET", "/"),
    ("GET", "/items"),
    ("GET", "/items/[id]"),
    ("POST", "/items"),
    ("GET", "/api/search"),
    ("POST", "/api/submit"),
    ("GET", "/api/status"),
    ("GET", "/about"),
    ("GET", "/login"),
    ("POST", "/login"),
]


def _format_row(row: list) -> str:
    """Format a CSV row matching Locust's output style: strings quoted, numbers bare."""
    parts = []
    for val in row:
        if isinstance(val, str):
            parts.append(f'"{val}"')
        elif isinstance(val, float):
            parts.append(f"{val:.2f}")
        else:
            parts.append(str(val))
    return ",".join(parts)


def _percentiles(median: int) -> List[int]:
    """Generate realistic ascending percentile values from a median response time."""
    multipliers = [1.00, 1.05, 1.10, 1.15, 1.25, 1.40, 1.60, 1.90, 2.20, 2.80, 3.50, 4.50]
    result = []
    prev = median
    for m in multipliers:
        val = max(prev, int(median * m * random.uniform(0.95, 1.05)))
        result.append(val)
        prev = val
    return result


def generate(
    output_path: Path,
    test_status: str = "passed",
    handler_def: Dict = None,
    num_endpoints: int = 5,
    **kwargs,
) -> None:
    """Generate a Locust stats CSV file (*_stats.csv format).

    Args:
        output_path: Path where the CSV file should be written
        test_status: 'passed', 'failed', or 'mixed'
        handler_def: Handler definition from handlers.yaml (unused here)
        num_endpoints: Number of endpoint rows to generate (excluding Aggregated)
        **kwargs: Additional parameters (ignored)
    """
    pool = (ENDPOINT_POOL * ((num_endpoints // len(ENDPOINT_POOL)) + 1))[:num_endpoints]

    rows = []
    total_requests = 0
    total_failures = 0
    total_rps = 0.0
    total_fps = 0.0

    for idx, (method, path) in enumerate(pool):
        req_count = random.randint(5, 50)

        if test_status == "failed":
            failure_count = random.randint(req_count // 2, req_count)
        elif test_status == "mixed" and idx % 3 == 1:
            failure_count = random.randint(1, max(1, req_count // 3))
        else:
            failure_count = 0

        base_ms = random.randint(150, 400) if method == "POST" else random.randint(50, 150)
        median = base_ms
        avg = int(base_ms * random.uniform(1.0, 1.3))
        min_t = int(base_ms * random.uniform(0.6, 0.9))
        max_t = int(base_ms * random.uniform(1.5, 3.0))
        content_size = random.randint(500, 5000) if method == "GET" else random.randint(50, 500)

        duration = random.uniform(30.0, 120.0)
        rps = round(req_count / duration, 2)
        fps = round(failure_count / duration, 2) if failure_count > 0 else 0.0

        row = [method, path, req_count, failure_count, median, avg, min_t, max_t,
               content_size, rps, fps] + _percentiles(median)
        rows.append(row)

        total_requests += req_count
        total_failures += failure_count
        total_rps += rps
        total_fps += fps

    agg_median = int(sum(r[4] for r in rows) / len(rows))
    agg_row = [
        "None", "Aggregated",
        total_requests, total_failures,
        agg_median,
        int(sum(r[5] for r in rows) / len(rows)),
        min(r[6] for r in rows),
        max(r[7] for r in rows),
        int(sum(r[8] for r in rows) / len(rows)),
        round(total_rps, 2), round(total_fps, 2),
    ] + _percentiles(agg_median)
    rows.append(agg_row)

    lines = [_format_row(HEADER)] + [_format_row(r) for r in rows]
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
        f.write("\n")
