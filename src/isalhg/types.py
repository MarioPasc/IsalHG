"""Type aliases used across the package.

Reserved for primitive aliases. Structured dataclasses live in the sub-package
that owns the concept (``datasets/schemas.py``, ``experiments/schemas.py``).
"""

from __future__ import annotations

from typing import TypeAlias

# Hypergraph primitives
NodeId: TypeAlias = int
EdgeId: TypeAlias = int
PointerIndex: TypeAlias = int
InstructionToken: TypeAlias = str
HyperedgeSet: TypeAlias = frozenset[NodeId]

# Iso-backend primitives
Fingerprint: TypeAlias = bytes
BackendName: TypeAlias = str

# Dataset primitives
DatasetName: TypeAlias = str
IsoClassId: TypeAlias = int

# Protocol primitives
ProtocolName: TypeAlias = str

# Reproducibility
Seed: TypeAlias = int
