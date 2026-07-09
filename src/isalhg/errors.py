"""Custom exception hierarchy for IsalHG.

All package-specific exceptions descend from ``IsalHGError``. Modules
should derive their own sub-hierarchies under this root rather than
raising bare ``Exception`` / ``RuntimeError``.
"""

from __future__ import annotations


class IsalHGError(Exception):
    """Base class for IsalHG-specific errors."""


# ---------------------------------------------------------------------------
# core/ — instruction set and virtual machine
# ---------------------------------------------------------------------------


class InvalidInstructionError(IsalHGError):
    """Raised when an instruction token violates the alphabet's constraints."""


class CanonicalizationTimeoutError(IsalHGError):
    """Raised when canonical-string computation exceeds its time budget."""


class AlgorithmUnavailableError(IsalHGError):
    """Raised when an H2S algorithm name is not registered (or fails to import)."""


class ArityMismatchError(IsalHGError):
    """Raised when an operation references more pointers than the machine has."""


class InvalidPointerError(IsalHGError):
    """Raised when a pointer index falls outside the 1..k range."""


class InvalidLabelError(IsalHGError):
    """Raised when a vertex or edge label is outside its declared vocabulary range."""


class CapacityError(IsalHGError):
    """Raised when a fixed-capacity container (CDLL, SparseHypergraph) is full."""


class DisconnectedHypergraphError(IsalHGError):
    """Raised when an operation requires a connected hypergraph (decision B11)."""


class VocabularyMismatchError(IsalHGError):
    """Raised when two hypergraphs declare incompatible label vocabularies."""


class HypergraphEditError(IsalHGError):
    """Raised when a structural edit operation violates a precondition.

    Covers the six unit edit operations on :class:`SparseHypergraph`
    (vertex/hyperedge insert-delete, incidence add-remove): deleting a
    non-isolated vertex, removing the last incidence of a hyperedge,
    referencing an out-of-range operand, or producing a duplicate
    ``(label, member-set)`` that would silently merge two hyperedges.
    """


# ---------------------------------------------------------------------------
# adapters/ — external library bridges
# ---------------------------------------------------------------------------


class AdapterError(IsalHGError):
    """Base class for adapter-layer failures."""


class AdapterDependencyMissingError(AdapterError):
    """Raised when an external hypergraph library is not installed."""


class AdapterTranslationError(AdapterError):
    """Raised when an external hypergraph cannot be translated faithfully."""


# ---------------------------------------------------------------------------
# iso_backends/ — isomorphism algorithm backends
# ---------------------------------------------------------------------------


class IsoBackendError(IsalHGError):
    """Base class for isomorphism-backend failures."""


class BackendUnavailableError(IsoBackendError):
    """Raised when a backend's binary or Python binding is missing."""


class BackendTimeoutError(IsoBackendError):
    """Raised when a backend exceeds its per-instance wall-clock budget."""


class BackendOutputParseError(IsoBackendError):
    """Raised when a subprocess backend emits unparseable output."""


# ---------------------------------------------------------------------------
# datasets/ — dataset loaders
# ---------------------------------------------------------------------------


class DatasetError(IsalHGError):
    """Base class for dataset-layer failures."""


class DatasetNotFoundError(DatasetError):
    """Raised when a dataset name is not registered."""


class DatasetIntegrityError(DatasetError):
    """Raised when a loaded dataset fails its integrity check."""


# ---------------------------------------------------------------------------
# protocols/ — benchmark protocols
# ---------------------------------------------------------------------------


class ProtocolError(IsalHGError):
    """Base class for benchmark-protocol failures."""


class ProtocolNotFoundError(ProtocolError):
    """Raised when a protocol name is not registered."""


class ProtocolPreconditionError(ProtocolError):
    """Raised when a backend/dataset pair does not satisfy a protocol's preconditions."""


# ---------------------------------------------------------------------------
# viz/ — visualisation backends
# ---------------------------------------------------------------------------


class VizError(IsalHGError):
    """Base class for visualisation-layer failures."""


class VizBackendUnavailableError(VizError):
    """Raised when a visualisation backend's library is not installed."""


class VizBackendNotFoundError(VizError):
    """Raised when a visualisation backend name is not registered."""


# ---------------------------------------------------------------------------
# metric_space/ — hypergraph distances and representations
# ---------------------------------------------------------------------------


class MetricSpaceError(IsalHGError):
    """Base class for metric-space (hypergraph-distance) failures."""


class DistanceUnavailableError(MetricSpaceError):
    """Raised when a distance name is not registered (or fails to import)."""


class DistanceComputationError(MetricSpaceError):
    """Raised when a distance computation fails for two given hypergraphs."""


class HGEDComputationError(MetricSpaceError):
    """Raised when a hypergraph-edit-distance oracle fails (e.g. solver timeout)."""


class RepresentationDependencyMissingError(MetricSpaceError):
    """Raised when a guarded optional dependency of a distance is not installed.

    Carries a concrete install hint in its message, mirroring
    :class:`AdapterDependencyMissingError`.
    """


class SubprocessRepresentationError(MetricSpaceError):
    """Raised when a pinned-environment subprocess distance fails or is unconfigured."""
