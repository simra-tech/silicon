#!/usr/bin/env python3
"""Recount the frozen comparator-offset campaign from its selected raw files."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (position - low) * (ordered[high] - ordered[low])


def extract_vos(raw_path: Path) -> float:
    rows: list[list[float]] = []
    with raw_path.open() as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            fields = line.split()
            if len(fields) != 6:
                raise ValueError(f"{raw_path.name}:{line_number}: expected 6 columns")
            row = [float(field) for field in fields]
            if not all(math.isfinite(value) for value in row):
                raise ValueError(f"{raw_path.name}:{line_number}: non-finite value")
            rows.append(row)

    if len(rows) != 1201:
        raise ValueError(f"{raw_path.name}: expected 1201 rows, found {len(rows)}")
    if not all(
        math.isclose(row[0], value, rel_tol=0.0, abs_tol=2e-15)
        for row in rows
        for value in (row[1], row[2], row[4])
    ):
        raise ValueError(f"{raw_path.name}: wrdata scale columns disagree")
    if not all(rows[index + 1][0] > rows[index][0] for index in range(1200)):
        raise ValueError(f"{raw_path.name}: sweep coordinate is not strictly increasing")

    crossings = [
        index
        for index in range(1200)
        if rows[index][3] == 0.0 or rows[index][3] * rows[index + 1][3] < 0.0
    ]
    if len(crossings) != 1:
        raise ValueError(f"{raw_path.name}: expected one crossing, found {len(crossings)}")

    index = crossings[0]
    x0, y0 = rows[index][0], rows[index][3]
    x1, y1 = rows[index + 1][0], rows[index + 1][3]
    return x0 - y0 * (x1 - x0) / (y1 - y0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, default=Path("offset-summary.csv"))
    args = parser.parse_args()

    root = args.directory.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    points_path = root / "comp_mc_campaign_n200_points_v4.tsv"

    records: list[dict[str, str]] = []
    complete_values: list[float] = []
    with points_path.open(newline="") as handle:
        points = list(csv.DictReader(handle, delimiter="\t"))

    if len(points) != 200 or len({row["seed"] for row in points}) != 200:
        raise ValueError("point manifest must contain 200 unique seeds")

    for point in points:
        value = ""
        if point["point_status"] == "complete":
            vos = extract_vos(root / point["selected_raw_file"])
            complete_values.append(vos)
            value = f"{vos * 1e3:.12f}"
        elif point["point_status"] != "unknown":
            raise ValueError(f"unsupported point status {point['point_status']!r}")
        records.append(
            {
                "seed": point["seed"],
                "point_status": point["point_status"],
                "reason_code": point["reason_code"],
                "selected_attempt_id": point["selected_attempt_id"],
                "vos_mV": value,
            }
        )

    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "seed",
                "point_status",
                "reason_code",
                "selected_attempt_id",
                "vos_mV",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(records)

    mean = statistics.mean(complete_values)
    sample_sd = statistics.stdev(complete_values)
    summary = {
        "planned_points": len(points),
        "complete_points": len(complete_values),
        "unknown_points": len(points) - len(complete_values),
        "mean_vos_mV_conditional": mean * 1e3,
        "sample_sd_vos_mV_conditional": sample_sd * 1e3,
        "se_mean_mV_conditional": sample_sd / math.sqrt(len(complete_values)) * 1e3,
        "median_vos_mV_conditional": statistics.median(complete_values) * 1e3,
        "empirical_q2_5_mV_conditional": quantile(complete_values, 0.025) * 1e3,
        "empirical_q97_5_mV_conditional": quantile(complete_values, 0.975) * 1e3,
        "minimum_vos_mV_conditional": min(complete_values) * 1e3,
        "maximum_vos_mV_conditional": max(complete_values) * 1e3,
        "specification_status": "not-evaluated",
        "engineering_status": "unknown",
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
