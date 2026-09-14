"""Validate a TLC Yellow Taxi partition and quarantine invalid rows."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import yaml


def load_config(path: Path) -> dict[str, Any]:
    """Load YAML configuration."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise TypeError("configuration root must be an object")

    return payload


def month_bounds(month: str) -> tuple[datetime, datetime]:
    """Return naive local-clock bounds matching TLC timestamp semantics."""
    year, month_number = map(int, month.split("-"))

    # TLC Parquet timestamps are handled as timezone-naive local wall-clock
    # values here. Do not attach UTC merely to satisfy linting.
    start = datetime(year, month_number, 1)  # noqa: DTZ001

    if month_number == 12:
        end = datetime(year + 1, 1, 1)  # noqa: DTZ001
    else:
        end = datetime(year, month_number + 1, 1)  # noqa: DTZ001

    return start, end

def validate_partition(
    path: Path,
    month: str,
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Validate temporal eligibility for one TLC partition."""
    table = pq.read_table(path)

    pickup = table["tpep_pickup_datetime"]
    dropoff = table["tpep_dropoff_datetime"]

    start, end = month_bounds(month)

    pickup_not_null = pc.invert(pc.is_null(pickup))
    dropoff_not_null = pc.invert(pc.is_null(dropoff))

    pickup_after_start = pc.greater_equal(
        pickup,
        pa.scalar(start, type=pickup.type),
    )
    pickup_before_end = pc.less(
        pickup,
        pa.scalar(end, type=pickup.type),
    )

    valid_pickup_month = pc.and_(
        pickup_after_start,
        pickup_before_end,
    )

    valid_duration = pc.greater_equal(dropoff, pickup)

    valid_mask = pc.and_(
        pc.and_(pickup_not_null, dropoff_not_null),
        pc.and_(valid_pickup_month, valid_duration),
    )

    accepted = table.filter(valid_mask)
    rejected = table.filter(pc.invert(valid_mask))

    before_month_mask = pc.less(
        pickup,
        pa.scalar(start, type=pickup.type),
    )

    after_month_mask = pc.greater_equal(
        pickup,
        pa.scalar(end, type=pickup.type),
    )

    negative_duration_mask = pc.less(dropoff, pickup)

    metrics = {
        "partition": month,
        "input_rows": table.num_rows,
        "accepted_rows": accepted.num_rows,
        "rejected_rows": rejected.num_rows,
        "pickup_before_partition": pc.sum(
            pc.cast(before_month_mask, pa.int64())
        ).as_py(),
        "pickup_after_partition": pc.sum(
            pc.cast(after_month_mask, pa.int64())
        ).as_py(),
        "dropoff_before_pickup": pc.sum(
            pc.cast(negative_duration_mask, pa.int64())
        ).as_py(),
    }

    metrics["reconciliation_ok"] = (
        metrics["input_rows"]
        == metrics["accepted_rows"] + metrics["rejected_rows"]
    )

    metrics["rejection_rate"] = (
        metrics["rejected_rows"] / metrics["input_rows"]
        if metrics["input_rows"]
        else 0.0
    )

    return accepted, rejected, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/d1_smoke.yml"),
    )
    args = parser.parse_args()

    config = load_config(args.config)

    run = config["run"]
    month = str(config["tlc"]["months"][0])

    raw_path = Path(
        f"data/raw/tlc/yellow_tripdata_{month}.parquet"
    )

    _accepted, rejected, metrics = validate_partition(
        raw_path,
        month,
    )

    quarantine_path = Path(
        f"data/quarantine/tlc/yellow_tripdata_{month}_rejected.parquet"
    )
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)

    pq.write_table(rejected, quarantine_path)

    report_path = Path(
        f"reports/runs/{run['run_id']}_validation.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_path.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    print(f"Run ID: {run['run_id']}")
    print(f"Partition: {month}")
    print(f"Input rows: {metrics['input_rows']:,}")
    print(f"Accepted rows: {metrics['accepted_rows']:,}")
    print(f"Rejected rows: {metrics['rejected_rows']:,}")
    print(
        "Pickup before partition: "
        f"{metrics['pickup_before_partition']:,}"
    )
    print(
        "Pickup after partition: "
        f"{metrics['pickup_after_partition']:,}"
    )
    print(
        "Dropoff before pickup: "
        f"{metrics['dropoff_before_pickup']:,}"
    )
    print(
        f"Rejection rate: {metrics['rejection_rate']:.6%}"
    )
    print(
        f"Reconciliation OK: {metrics['reconciliation_ok']}"
    )
    print(f"Quarantine: {quarantine_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()