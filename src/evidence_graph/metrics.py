"""Metrics describing evidence-graph completeness."""

from evidence_graph.graph import EvidenceGraph


def node_count(graph: EvidenceGraph) -> int:
    """Return total number of evidence nodes."""
    return len(graph.nodes)


def edge_count(graph: EvidenceGraph) -> int:
    """Return total number of evidence relationships."""
    return len(graph.edges)


def count_by_kind(graph: EvidenceGraph) -> dict[str, int]:
    """Count evidence nodes by their declared kind."""
    counts: dict[str, int] = {}

    for node in graph.nodes:
        counts[node.kind] = counts.get(node.kind, 0) + 1

    return counts


def claim_traceability_rate(graph: EvidenceGraph) -> float:
    """
    Return the fraction of claim nodes reachable from at least one dataset node.

    This is a structural traceability measure, not a measure of scientific truth.
    """
    claims = graph.nodes_by_kind("claim")

    if not claims:
        return 0.0

    datasets = graph.nodes_by_kind("dataset")

    traceable = 0

    for claim in claims:
        if any(
            graph.has_path(dataset.node_id, claim.node_id)
            for dataset in datasets
        ):
            traceable += 1

    return traceable / len(claims)
