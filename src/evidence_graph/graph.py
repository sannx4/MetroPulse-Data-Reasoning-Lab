"""In-memory evidence graph with integrity checks."""

from collections import deque

from evidence_graph.models import EvidenceEdge, EvidenceNode


class EvidenceGraph:
    """Directed graph connecting portfolio evidence artifacts."""

    def __init__(self) -> None:
        self._nodes: dict[str, EvidenceNode] = {}
        self._edges: list[EvidenceEdge] = []

    @property
    def nodes(self) -> tuple[EvidenceNode, ...]:
        return tuple(self._nodes.values())

    @property
    def edges(self) -> tuple[EvidenceEdge, ...]:
        return tuple(self._edges)

    def add_node(self, node: EvidenceNode) -> None:
        """Add a unique node to the graph."""
        if node.node_id in self._nodes:
            raise ValueError(f"duplicate node_id: {node.node_id}")

        self._nodes[node.node_id] = node

    def add_edge(self, edge: EvidenceEdge) -> None:
        """Add an edge only when both referenced nodes exist."""
        if edge.source not in self._nodes:
            raise ValueError(f"unknown source node: {edge.source}")

        if edge.target not in self._nodes:
            raise ValueError(f"unknown target node: {edge.target}")

        if edge in self._edges:
            raise ValueError(
                "duplicate edge: "
                f"{edge.source} -[{edge.relation}]-> {edge.target}"
            )

        self._edges.append(edge)

    def get_node(self, node_id: str) -> EvidenceNode:
        """Return one node by ID."""
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"unknown node_id: {node_id}") from exc

    def nodes_by_kind(self, kind: str) -> tuple[EvidenceNode, ...]:
        """Return all nodes matching a particular evidence kind."""
        return tuple(node for node in self._nodes.values() if node.kind == kind)

    def outgoing(self, node_id: str) -> tuple[EvidenceEdge, ...]:
        """Return edges leaving a node."""
        self.get_node(node_id)

        return tuple(edge for edge in self._edges if edge.source == node_id)

    def incoming(self, node_id: str) -> tuple[EvidenceEdge, ...]:
        """Return edges pointing to a node."""
        self.get_node(node_id)

        return tuple(edge for edge in self._edges if edge.target == node_id)

    def has_path(self, source: str, target: str) -> bool:
        """Return whether a directed path exists between two nodes."""
        self.get_node(source)
        self.get_node(target)

        if source == target:
            return True

        adjacency: dict[str, list[str]] = {}

        for edge in self._edges:
            adjacency.setdefault(edge.source, []).append(edge.target)

        queue: deque[str] = deque([source])
        visited = {source}

        while queue:
            current = queue.popleft()

            for neighbor in adjacency.get(current, []):
                if neighbor == target:
                    return True

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False
