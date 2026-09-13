"""Load evidence graphs from structured data."""

import json
from pathlib import Path
from typing import Any

from evidence_graph.graph import EvidenceGraph
from evidence_graph.models import EvidenceEdge, EvidenceNode


def graph_from_dict(payload: dict[str, Any]) -> EvidenceGraph:
    """Build an EvidenceGraph from a validated dictionary-like payload."""
    graph = EvidenceGraph()

    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])

    if not isinstance(nodes, list):
        raise TypeError("'nodes' must be a list")

    if not isinstance(edges, list):
        raise TypeError("'edges' must be a list")

    for raw_node in nodes:
        if not isinstance(raw_node, dict):
            raise TypeError("each node must be an object")

        try:
            node = EvidenceNode(
                node_id=str(raw_node["id"]),
                kind=str(raw_node["kind"]),
                label=str(raw_node["label"]),
                metadata=dict(raw_node.get("metadata", {})),
            )
        except KeyError as exc:
            raise ValueError(
                f"node missing required field: {exc.args[0]}"
            ) from exc

        graph.add_node(node)

    for raw_edge in edges:
        if not isinstance(raw_edge, dict):
            raise TypeError("each edge must be an object")

        try:
            edge = EvidenceEdge(
                source=str(raw_edge["source"]),
                target=str(raw_edge["target"]),
                relation=str(raw_edge["relation"]),
            )
        except KeyError as exc:
            raise ValueError(
                f"edge missing required field: {exc.args[0]}"
            ) from exc

        graph.add_edge(edge)

    return graph


def load_graph(path: Path) -> EvidenceGraph:
    """Load an evidence graph from a JSON document."""
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise TypeError("evidence graph document must contain an object")

    return graph_from_dict(payload)
