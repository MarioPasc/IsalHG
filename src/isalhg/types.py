"""Type aliases used across the package.

Reserved for primitive aliases. Structured dataclasses live in the sub-package
that owns the concept (``datasets/schemas.py``, ``experiments/schemas.py``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

# Hypergraph primitives
NodeId: TypeAlias = int
EdgeId: TypeAlias = int
PointerIndex: TypeAlias = int
InstructionToken: TypeAlias = str
HyperedgeSet: TypeAlias = frozenset[NodeId]

# Label primitives (decision I45). Labels are always ``int`` IDs in
# ``[0, |Sigma_v|)`` / ``[0, |Sigma_e|)``; the semantic-string layer lives in
# ``datasets.schemas.LabelVocabulary`` and never reaches ``core/``.
VertexLabel: TypeAlias = int
EdgeLabel: TypeAlias = int

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

# Token sequence — forward-referenced to break the import cycle with
# ``core.instructions``. Concrete subclasses are defined there.
if TYPE_CHECKING:
    from isalhg.core.instructions import Token

    TokenSequence: TypeAlias = tuple[Token, ...]
else:
    TokenSequence: TypeAlias = tuple
