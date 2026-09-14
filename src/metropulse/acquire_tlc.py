"""Acquire an immutable NYC TLC Yellow Taxi partition and record provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import yaml

TLC_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def download_file(url: str, destination: Path) -> None:
    """Download to a temporary file and atomically promote on success."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "MetroPulse/0.1 portfolio research"},
    )

    try:
        with (
            urllib.request.urlopen(request, timeout=120) as response,
            temporary.open("wb") as output,
        ):
                    shutil.copyfileobj(response, output)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def timestamp_bounds(
    path: Path,
    column: str,
) -> tuple[str | None, str | None]:
    """Return exact min/max timestamps for one Parquet column."""
    table = pq.read_table(path, columns=[column])

    result = pc.min_max(table[column]).as_py()

    if result is None:
        return None, None

    minimum = result["min"]
    maximum = result["max"]

    return (
        minimum.isoformat() if minimum is not None else None,
        maximum.isoformat() if maximum is not None else None,
    )


def inspect_parquet(path: Path) -> dict[str, Any]:
    """Collect row, schema, byte and temporal metadata."""
    parquet = pq.ParquetFile(path)

    pickup_min, pickup_max = timestamp_bounds(
        path,
        "tpep_pickup_datetime",
    )
    dropoff_min, dropoff_max = timestamp_bounds(
        path,
        "tpep_dropoff_datetime",
    )

    return {
        "rows": parquet.metadata.num_rows,
        "row_groups": parquet.metadata.num_row_groups,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "pickup_min": pickup_min,
        "pickup_max": pickup_max,
        "dropoff_min": dropoff_min,
        "dropoff_max": dropoff_max,
        "schema": parquet.schema_arrow,
    }


def write_schema(schema: pa.Schema, destination: Path) -> None:
    """Persist a machine-readable schema description."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "fields": [
            {
                "name": field.name,
                "type": str(field.type),
                "nullable": field.nullable,
            }
            for field in schema
        ]
    }

    destination.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def write_manifest(row: dict[str, Any], path: Path) -> None:
    """Upsert one acquired source object into the raw manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)

    new_table = pa.Table.from_pylist([row])

    if not path.exists():
        pq.write_table(new_table, path)
        return

    existing = pq.read_table(path)
    rows = existing.to_pylist()

    rows = [
        existing_row
        for existing_row in rows
        if not (
            existing_row["dataset_id"] == row["dataset_id"]
            and existing_row["period"] == row["period"]
        )
    ]

    rows.append(row)

    pq.write_table(pa.Table.from_pylist(rows), path)


def load_config(path: Path) -> dict[str, Any]:
    """Load and minimally validate the D1 configuration."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise TypeError("configuration root must be an object")

    return payload


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
    tlc = config["tlc"]

    if run["tier"] != "smoke":
        raise ValueError("this command currently supports smoke tier only")

    months = tlc["months"]

    if len(months) != 1:
        raise ValueError("D1 smoke run must contain exactly one TLC month")

    month = str(months[0])

    source_url = (
        f"{TLC_BASE_URL}/yellow_tripdata_{month}.parquet"
    )

    raw_path = Path(
        f"data/raw/tlc/yellow_tripdata_{month}.parquet"
    )

    print(f"Run ID: {run['run_id']}")
    print(f"Dataset: {tlc['dataset_id']}")
    print(f"Period: {month}")
    print(f"Destination: {raw_path}")

    if raw_path.exists():
        print("Raw file already exists; preserving immutable local copy.")
    else:
        print("Downloading authoritative TLC partition...")
        download_file(source_url, raw_path)

    metadata = inspect_parquet(raw_path)

    schema_path = Path(
        f"data/schemas/tlc_yellow_{month}.json"
    )

    write_schema(metadata["schema"], schema_path)

    retrieved_at = datetime.now(UTC).isoformat()

    manifest_row = {
        "dataset_id": "TLC",
        "publisher": "NYC Taxi and Limousine Commission",
        "object_name": raw_path.name,
        "period": month,
        "source_url": source_url,
        "retrieved_at_utc": retrieved_at,
        "bytes": metadata["bytes"],
        "sha256": metadata["sha256"],
        "rows": metadata["rows"],
        "pickup_min": metadata["pickup_min"],
        "pickup_max": metadata["pickup_max"],
        "dropoff_min": metadata["dropoff_min"],
        "dropoff_max": metadata["dropoff_max"],
        "run_id": run["run_id"],
        "tier": run["tier"],
        "supports_portfolio_claims": bool(
            run["supports_portfolio_claims"]
        ),
    }

    write_manifest(
        manifest_row,
        Path("data/raw_manifest.parquet"),
    )

    print()
    print("Acquisition complete")
    print(f"Rows: {metadata['rows']:,}")
    print(f"Bytes: {metadata['bytes']:,}")
    print(f"SHA-256: {metadata['sha256']}")
    print(
        "Pickup range: "
        f"{metadata['pickup_min']} -> {metadata['pickup_max']}"
    )
    print(
        "Dropoff range: "
        f"{metadata['dropoff_min']} -> {metadata['dropoff_max']}"
    )
    print(f"Schema: {schema_path}")
    print("Manifest: data/raw_manifest.parquet")
    print("Portfolio claims supported: NO")
    

if __name__ == "__main__":
    main()
