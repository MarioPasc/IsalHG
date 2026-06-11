"""End-to-end: SparseHypergraph -> TracesLeviBackend.fingerprint (subprocess)."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.subprocess]


def test_placeholder() -> None:
    pytest.skip("not implemented yet")
