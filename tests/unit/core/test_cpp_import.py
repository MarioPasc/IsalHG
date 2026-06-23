"""Phase-0 smoke test: the native ``_core`` extension is importable.

The extension is built by scikit-build-core during ``pip install -e``.
A failure here means the C++ build pipeline is broken — investigate
before chasing later test failures.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_core_extension_imports() -> None:
    import isalhg._core as _core

    assert hasattr(_core, "ping")
    assert _core.ping() == "pong"
