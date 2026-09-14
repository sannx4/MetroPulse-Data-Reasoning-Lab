
## Engineering validation — evidence graph

Date: 2026-09-13

### Tests
Command:

    uv run pytest -v

Result:

- 18 tests collected
- 18 passed
- 0 failed

Coverage of current tests:
- evidence node creation/retrieval
- duplicate node rejection
- invalid edge references
- duplicate edge rejection
- directed path traversal
- node filtering by kind
- package imports
- structured graph loading
- malformed loader input
- unknown edge references
- JSON loading
- node/edge metrics
- evidence-kind counts
- claim traceability metrics

### Lint
Command:

    uv run ruff check .

Result:

    All checks passed!

### Static typing
Command:

    uv run mypy src

Result:

    Success: no issues found in 5 source files

### Scope limitation
These checks validate the D1 evidence-graph implementation only.
They do not yet constitute TLC/NOAA real-data validation or support any analytical claim.

## TLC real-data smoke validation

Run ID: `RUN-20260913-TLC-SMOKE-001`

Dataset: NYC TLC Yellow Taxi Trip Records  
Partition: `2022-01`  
Tier: smoke  
Portfolio claims supported: no

### Source acquisition

- Input rows: 2,463,931
- Source bytes: 38,139,949
- SHA-256: `797d6f008e67c3e3371b7f957ab97dbc2b38a9fb0ac083cb5eae4b0297b32372`
- Raw pickup range: 2008-12-31T22:23:09 → 2022-05-18T20:41:57
- Raw dropoff range: 2008-12-31T23:06:56 → 2022-05-18T20:47:45

### Temporal validation

Eligibility rule:

    2022-01-01 00:00:00 <= pickup_datetime < 2022-02-01 00:00:00
    AND dropoff_datetime >= pickup_datetime

Results:

- Accepted rows: 2,462,526
- Rejected rows: 1,405
- Rejection rate: 0.057023%
- Pickup before partition: 38
- Pickup after partition: 14
- Dropoff before pickup: 1,353

### Reconciliation

    2,462,526 + 1,405 = 2,463,931

Reconciliation status: PASS

### Negative finding

The nominal `2022-01` TLC source partition contains records with event
timestamps outside January 2022, including extreme historical timestamps.
The pipeline therefore does not trust filename partition membership alone.

Rejected rows are quarantined rather than silently deleted.

### Limitation

This is a smoke-tier pipeline-validation run over one TLC partition.
It does not support final portfolio analytical claims and does not yet
include NOAA weather joins.
