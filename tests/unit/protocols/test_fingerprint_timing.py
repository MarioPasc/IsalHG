"""Unit tests for :mod:`isalhg.protocols.fingerprint_timing`."""

from __future__ import annotations

import pytest

from isalhg.datasets.synthetic.erdos_renyi import UniformErdosRenyiHypergraphs
from isalhg.iso_backends.registry import get_backend
from isalhg.protocols.fingerprint_timing import FingerprintTimingProtocol
from isalhg.protocols.registry import get_protocol

pytestmark = pytest.mark.unit


REQUIRED_KEYS: tuple[str, ...] = (
    "n_items",
    "n_dnf",
    "n_positive_pair_checked",
    "median_time_s",
    "iqr_time_s",
    "peak_rss_bytes",
    "fp_bytes_length",
    "repeats",
    "timeout_s",
    "positive_pair_passes",
    "positive_pair_failures",
    "dnf_items",
    "per_item",
)


class TestConstruction:
    def test_rejects_bad_timeout(self) -> None:
        with pytest.raises(ValueError, match="timeout_s"):
            FingerprintTimingProtocol(timeout_s=0.0)

    def test_rejects_bad_repeats(self) -> None:
        with pytest.raises(ValueError, match="repeats"):
            FingerprintTimingProtocol(repeats=0)


class TestMeasureSmoke:
    def test_isalhg_backend_small_er(self) -> None:
        # n=6, r=3 is small enough for sub-second IsalHG fingerprinting and
        # produces a connected hypergraph at c=2 almost always.
        ds = UniformErdosRenyiHypergraphs(n=6, r=3, c=2, seed=0)
        backend = get_backend("isalhg")
        proto = FingerprintTimingProtocol(timeout_s=30.0, repeats=2, check_positive_pair=True)
        result = proto.measure(backend, ds, seed=0)

        assert result.protocol == "fingerprint_timing"
        assert result.backend == "isalhg"
        assert result.dataset == "random_erdos_renyi"
        assert result.seed == 0
        assert result.wall_clock_s > 0

        meas = result.measurements
        for key in REQUIRED_KEYS:
            assert key in meas, f"missing key {key!r}"

        assert meas["n_items"] == 1
        assert meas["n_dnf"] == 0
        assert meas["repeats"] == 2
        assert meas["timeout_s"] == 30.0
        assert meas["n_positive_pair_checked"] == 1
        assert meas["positive_pair_passes"] == 1
        assert meas["positive_pair_failures"] == []
        assert meas["median_time_s"] is not None
        assert meas["median_time_s"] >= 0.0
        assert meas["fp_bytes_length"] is not None
        assert meas["fp_bytes_length"] > 0

        assert len(meas["per_item"]) == 1
        row = meas["per_item"][0]
        assert row["dnf"] is False
        assert row["positive_pair_ok"] is True
        assert row["fp_bytes_length"] == meas["fp_bytes_length"]

    def test_positive_pair_check_disabled(self) -> None:
        ds = UniformErdosRenyiHypergraphs(n=5, r=2, c=2, seed=0)
        backend = get_backend("isalhg")
        proto = FingerprintTimingProtocol(timeout_s=10.0, repeats=1, check_positive_pair=False)
        result = proto.measure(backend, ds, seed=0)
        meas = result.measurements
        assert meas["n_positive_pair_checked"] == 0
        assert meas["positive_pair_passes"] == 0
        assert meas["per_item"][0]["positive_pair_ok"] is None


class TestRegistry:
    def test_registered_under_fingerprint_timing(self) -> None:
        proto = get_protocol(
            "fingerprint_timing",
            {"timeout_s": 5.0, "repeats": 1, "check_positive_pair": False},
        )
        assert isinstance(proto, FingerprintTimingProtocol)
        assert proto.name == "fingerprint_timing"
