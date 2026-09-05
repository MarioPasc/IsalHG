"""Exception hierarchy for :mod:`isalhg.generation`.

The repo convention is one hierarchy in :mod:`isalhg.errors`, rooted at
``IsalHGError``. These live here instead because ``isalhg/errors.py`` belongs to
a different owner in the wave that added this package; they still descend from
``IsalHGError``, so ``except IsalHGError`` catches them exactly as it catches
every other package's errors, and folding them into the central module later is
a move with no call-site consequences.
"""

from __future__ import annotations

from isalhg.errors import IsalHGError


class GenerationError(IsalHGError):
    """Root of the generation package's failures."""


class StrictDecodeError(GenerationError):
    """A flat incidence-list sequence violated the baseline grammar.

    Carried for callers that want the *reason* a sequence was rejected.
    :func:`isalhg.generation.incidence_baseline.strict_decode` itself returns
    ``None`` rather than raising -- rejection is the measured outcome of RQ6's
    baseline arm, not an error condition -- and
    :func:`isalhg.generation.incidence_baseline.strict_decode_reason` reports
    which rule fired.
    """


__all__ = ["GenerationError", "StrictDecodeError"]
