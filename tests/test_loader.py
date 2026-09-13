import json

import pytest

from evidence_graph.loader import graph_from_dict, load_graph


def test_graph_from_dict_loads_nodes_and_edges() -> None:
    payload = {
        "nodes": [
            {
                "id": "dataset-tlc",
                "kind": "dataset",
                "label": "NYC TLC Yellow Taxi",
            },
            {
                "id": "run-001",
                "kind": "run",
                "label": "D1 validation run",
            },
        ],
        "edges": [
            {
                "source": "dataset-tlc",
                "target": "run-001",
                "relation": "used_by",
            }
        ],
    }

    graph = graph_from_dict(payload)

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1


def test_missing_required_node_field_is_rejected() -> None:
    payload = {
        "nodes": [
            {
                "id": "dataset-tlc",
                "kind": "dataset",
            }
        ],
        "edges": [],
    }

    with pytest.raises(ValueError, match="missing required field"):
        graph_from_dict(payload)


def test_invalid_nodes_collection_is_rejected() -> None:
    payload = {
        "nodes": {},
        "edges": [],
    }

    with pytest.raises(TypeError, match="'nodes' must be a list"):
        graph_from_dict(payload)


def test_unknown_edge_reference_is_rejected() -> None:
    payload = {
        "nodes": [
            {
                "id": "dataset-tlc",
                "kind": "dataset",
                "label": "TLC",
            }
        ],
        "edges": [
            {
                "source": "dataset-tlc",
                "target": "missing-run",
                "relation": "used_by",
            }
        ],
    }

    with pytest.raises(ValueError, match="unknown target node"):
        graph_from_dict(payload)


def test_load_graph_reads_json_file(tmp_path) -> None:
    path = tmp_path / "graph.json"

    payload = {
        "nodes": [
            {
                "id": "dataset-tlc",
                "kind": "dataset",
                "label": "TLC",
            }
        ],
        "edges": [],
    }

    path.write_text(json.dumps(payload), encoding="utf-8")

    graph = load_graph(path)

    assert len(graph.nodes) == 1
    assert graph.get_node("dataset-tlc").kind == "dataset"
