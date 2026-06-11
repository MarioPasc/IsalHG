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


class ArityMismatchError(IsalHGError):
    """Raised when an operation references more pointers than the machine has."""


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
