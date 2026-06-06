"""Type aliases used across the package."""

from __future__ import annotations

from typing import TypeAlias

NodeId: TypeAlias = int
EdgeId: TypeAlias = int
PointerIndex: TypeAlias = int
InstructionToken: TypeAlias = str
HyperedgeSet: TypeAlias = frozenset[NodeId]
