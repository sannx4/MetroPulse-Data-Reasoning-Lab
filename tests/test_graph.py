import pytest

from evidence_graph.graph import EvidenceGraph
from evidence_graph.models import EvidenceEdge, EvidenceNode


def make_node(node_id: str, kind: str = "artifact") -> EvidenceNode:
    return EvidenceNode(
        node_id=node_id,
        kind=kind,
        label=node_id,
    )


def test_add_and_get_node() -> None:
    graph = EvidenceGraph()

    node = make_node("dataset-tlc", "dataset")
    graph.add_node(node)

    assert graph.get_node("dataset-tlc") == node


def test_duplicate_node_is_rejected() -> None:
    graph = EvidenceGraph()
    node = make_node("dataset-tlc", "dataset")

    graph.add_node(node)

    with pytest.raises(ValueError, match="duplicate node_id"):
        graph.add_node(node)


def test_edge_requires_existing_source() -> None:
    graph = EvidenceGraph()

    graph.add_node(make_node("run-001", "run"))

    with pytest.raises(ValueError, match="unknown source node"):
        graph.add_edge(
            EvidenceEdge(
                source="dataset-tlc",
                target="run-001",
                relation="used_by",
            )
        )


def test_edge_requires_existing_target() -> None:
    graph = EvidenceGraph()

    graph.add_node(make_node("dataset-tlc", "dataset"))

    with pytest.raises(ValueError, match="unknown target node"):
        graph.add_edge(
            EvidenceEdge(
                source="dataset-tlc",
                target="run-001",
                relation="used_by",
            )
        )


def test_duplicate_edge_is_rejected() -> None:
    graph = EvidenceGraph()

    graph.add_node(make_node("dataset-tlc", "dataset"))
    graph.add_node(make_node("run-001", "run"))

    edge = EvidenceEdge(
        source="dataset-tlc",
        target="run-001",
        relation="used_by",
    )

    graph.add_edge(edge)

    with pytest.raises(ValueError, match="duplicate edge"):
        graph.add_edge(edge)


def test_directed_path_exists() -> None:
    graph = EvidenceGraph()

    graph.add_node(make_node("dataset-tlc", "dataset"))
    graph.add_node(make_node("run-001", "run"))
    graph.add_node(make_node("artifact-001"))
    graph.add_node(make_node("claim-001", "claim"))

    graph.add_edge(
        EvidenceEdge("dataset-tlc", "run-001", "used_by")
    )
    graph.add_edge(
        EvidenceEdge("run-001", "artifact-001", "produced")
    )
    graph.add_edge(
        EvidenceEdge("artifact-001", "claim-001", "supports")
    )

    assert graph.has_path("dataset-tlc", "claim-001") is True
    assert graph.has_path("claim-001", "dataset-tlc") is False


def test_nodes_can_be_filtered_by_kind() -> None:
    graph = EvidenceGraph()

    graph.add_node(make_node("dataset-tlc", "dataset"))
    graph.add_node(make_node("dataset-noaa", "dataset"))
    graph.add_node(make_node("run-001", "run"))

    datasets = graph.nodes_by_kind("dataset")

    assert len(datasets) == 2
    assert {node.node_id for node in datasets} == {
        "dataset-tlc",
        "dataset-noaa",
    }
