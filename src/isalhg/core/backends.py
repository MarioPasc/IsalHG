"""Backend selection for the canonical-string algorithm.

Each user-facing function in :mod:`isalhg.core` (``canonical_string``,
``greedy_h2s``, ``wl_hash``, ``wl_partition``, ``max_xi_nodes``,
``hypergraph_to_string``) accepts a ``backend=`` keyword to choose
between the pure-Python reference implementation and the C++ extension
(``isalhg.core._core``). The default backend is ``"cpp"``.

Both implementations live under :mod:`isalhg.core`:

- Python reference: regular Python functions in each module, named
  ``_python_<fn>`` (kept for differential tests and inspection).
- C++ extension: native module ``isalhg.core._core`` plus a thin Python
  wrapper named ``_cpp_<fn>`` in each module (handles SHG view
  construction and token re-parsing).

Adding a new backend
--------------------

Each module owns a ``_<NAME>_BACKENDS`` dict that maps backend names to
implementation callables. To add a backend (e.g. a Rust port), append a
new entry to that dict at import time::

    from isalhg.core.hypergraph_to_string import _GREEDY_H2S_BACKENDS
    _GREEDY_H2S_BACKENDS["rust"] = _rust_greedy_h2s

The dispatcher picks the entry up on the next call.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, TypeVar

Backend = Literal["python", "cpp"]
"""Type alias for the ``backend=`` keyword across the package."""

DEFAULT_BACKEND: Backend = "cpp"
"""The default backend used when ``backend=`` is omitted."""


T = TypeVar("T")


def resolve(backend: str | None, registry: dict[str, Callable[..., T]]) -> Callable[..., T]:
    """Return the implementation registered under ``backend``.

    Parameters
    ----------
    backend : str or None
        Backend name. ``None`` resolves to :data:`DEFAULT_BACKEND`.
    registry : dict[str, callable]
        The per-module dispatch table.

    Returns
    -------
    callable
        The chosen implementation.

    Raises
    ------
    ValueError
        When ``backend`` is not a key of ``registry``.
    """
    chosen = DEFAULT_BACKEND if backend is None else backend
    impl = registry.get(chosen)
    if impl is None:
        valid = ", ".join(sorted(registry))
        raise ValueError(f"unknown backend {chosen!r}; valid options: {valid}")
    return impl
