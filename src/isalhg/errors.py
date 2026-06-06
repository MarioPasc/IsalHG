"""Custom exception hierarchy for IsalHG."""


class IsalHGError(Exception):
    """Base class for IsalHG-specific errors."""


class InvalidInstructionError(IsalHGError):
    """Raised when an instruction token violates the alphabet's constraints."""


class CanonicalizationTimeoutError(IsalHGError):
    """Raised when canonical-string computation exceeds its time budget."""


class ArityMismatchError(IsalHGError):
    """Raised when an operation references more pointers than the machine has."""
