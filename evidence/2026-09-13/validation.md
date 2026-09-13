
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
