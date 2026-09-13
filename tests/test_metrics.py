import pytest

from evidence_graph.graph import EvidenceGraph
from evidence_graph.metrics import (
    claim_traceability_rate,
    count_by_kind,
    edge_count,
    node_count,
)
from evidence_graph.models import EvidenceEdge, EvidenceNode


def add_node(
    graph: EvidenceGraph,
    node_id: str,
    kind: str,
) -> None:
    graph.add_node(
        EvidenceNode(
            node_id=node_id,
            kind=kind,
            label=node_id,
        )
    )


def test_node_and_edge_counts() -> None:
    graph = EvidenceGraph()

    add_node(graph, "dataset-tlc", "dataset")
    add_node(graph, "run-001", "run")

    graph.add_edge(
        EvidenceEdge(
            source="dataset-tlc",
            target="run-001",
            relation="used_by",
        )
    )

    assert node_count(graph) == 2
    assert edge_count(graph) == 1


def test_count_by_kind() -> None:
    graph = EvidenceGraph()

    add_node(graph, "dataset-tlc", "dataset")
    add_node(graph, "dataset-noaa", "dataset")
    add_node(graph, "run-001", "run")

    assert count_by_kind(graph) == {
        "dataset": 2,
        "run": 1,
    }


def test_traceability_rate_is_zero_without_claims() -> None:
    graph = EvidenceGraph()

    add_node(graph, "dataset-tlc", "dataset")

    assert claim_traceability_rate(graph) == 0.0


def test_fully_traceable_claims_return_one() -> None:
    graph = EvidenceGraph()

    add_node(graph, "dataset-tlc", "dataset")
    add_node(graph, "run-001", "run")
    add_node(graph, "artifact-001", "artifact")
    add_node(graph, "claim-001", "claim")

    graph.add_edge(
        EvidenceEdge("dataset-tlc", "run-001", "used_by")
    )
    graph.add_edge(
        EvidenceEdge("run-001", "artifact-001", "produced")
    )
    graph.add_edge(
        EvidenceEdge("artifact-001", "claim-001", "supports")
    )

    assert claim_traceability_rate(graph) == 1.0


def test_partial_traceability_is_calculated_correctly() -> None:
    graph = EvidenceGraph()

    add_node(graph, "dataset-tlc", "dataset")
    add_node(graph, "artifact-001", "artifact")
    add_node(graph, "claim-001", "claim")
    add_node(graph, "claim-002", "claim")

    graph.add_edge(
        EvidenceEdge("dataset-tlc", "artifact-001", "produced")
    )
    graph.add_edge(
        EvidenceEdge("artifact-001", "claim-001", "supports")
    )

    assert claim_traceability_rate(graph) == pytest.approx(0.5)
