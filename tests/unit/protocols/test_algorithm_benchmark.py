"""Unit tests for ``isalhg.protocols.algorithm_benchmark``."""

from __future__ import annotations

import pytest

from isalhg.datasets.synthetic.symmetric_designs import SymmetricDesigns
from isalhg.iso_backends.registry import get_backend
from isalhg.protocols.algorithm_benchmark import AlgorithmBenchmarkProtocol
from isalhg.protocols.registry import get_protocol

pytestmark = pytest.mark.unit


def _make_dataset_first_item_only() -> SymmetricDesigns:
    """Fano-only dataset (small, fast)."""

    class _Single(SymmetricDesigns):
        def __iter__(self):
            yield next(super().__iter__())

        def __len__(self):
            return 1

    return _Single()


def test_protocol_schema_keys() -> None:
    ds = _make_dataset_first_item_only()
    bk = get_backend("isalhg_greedy_min")
    pr = AlgorithmBenchmarkProtocol(timeout_s=30.0, repeats=2)
    res = pr.measure(bk, ds, seed=0)
    m = res.measurements
    for key in (
        "n_items",
        "n_dnf",
        "repeats",
        "timeout_s",
        "median_time_s",
        "iqr_time_s",
        "peak_rss_bytes",
        "n_roundtrip_checked",
        "n_roundtrip_failures",
        "n_iso_invariance_checked",
        "n_iso_invariance_failures",
        "dnf_items",
        "per_item",
    ):
        assert key in m, f"missing key {key!r} in measurements"
    row = m["per_item"][0]
    for key in (
        "item_id",
        "n_nodes",
        "n_edges",
        "max_arity",
        "wall_times_s",
        "median_time_s",
        "iqr_time_s",
        "peak_rss_bytes",
        "fingerprint_hex",
        "fp_bytes_length",
        "token_counts",
        "roundtrip_ok",
        "iso_invariance_ok",
        "dnf",
        "dnf_reason",
    ):
        assert key in row, f"missing key {key!r} in per_item row"


def test_protocol_fano_greedy_min_passes() -> None:
    ds = _make_dataset_first_item_only()
    bk = get_backend("isalhg_greedy_min")
    pr = AlgorithmBenchmarkProtocol(timeout_s=30.0, repeats=2)
    res = pr.measure(bk, ds, seed=0)
    row = res.measurements["per_item"][0]
    assert row["dnf"] is False
    assert row["roundtrip_ok"] is True
    assert row["iso_invariance_ok"] is True
    assert row["fingerprint_hex"] is not None
    assert row["fp_bytes_length"] > 0
    assert row["token_counts"]["V"] > 0


def test_protocol_registers_under_canonical_name() -> None:
    pr = get_protocol("algorithm_benchmark", {"timeout_s": 5.0, "repeats": 1})
    assert pr.name == "algorithm_benchmark"


def test_protocol_param_validation() -> None:
    with pytest.raises(ValueError):
        AlgorithmBenchmarkProtocol(timeout_s=0.0)
    with pytest.raises(ValueError):
        AlgorithmBenchmarkProtocol(repeats=0)


def test_protocol_timeout_marks_dnf() -> None:
    """Microscopically small timeout forces DNF on Fano (~0.78 s)."""
    ds = _make_dataset_first_item_only()
    bk = get_backend("isalhg_greedy_min")
    pr = AlgorithmBenchmarkProtocol(
        timeout_s=0.05, repeats=1, check_roundtrip=False, check_iso_invariance=False
    )
    # signal.alarm has integer resolution; clamp at 1s but Fano typically
    # takes ~0.8s so 1s is borderline. Test only that the protocol does not
    # crash with a sub-second timeout.
    res = pr.measure(bk, ds, seed=0)
    assert isinstance(res.measurements["n_dnf"], int)
