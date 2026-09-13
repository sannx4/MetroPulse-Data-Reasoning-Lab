"""Core data models for the portfolio evidence graph."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class EvidenceNode:
    """A uniquely identifiable item of portfolio evidence."""

    node_id: str
    kind: str
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must not be empty")
        if not self.kind.strip():
            raise ValueError("kind must not be empty")
        if not self.label.strip():
            raise ValueError("label must not be empty")


@dataclass(frozen=True, slots=True)
class EvidenceEdge:
    """A directed relationship between two evidence nodes."""

    source: str
    target: str
    relation: str

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source must not be empty")
        if not self.target.strip():
            raise ValueError("target must not be empty")
        if not self.relation.strip():
            raise ValueError("relation must not be empty")
