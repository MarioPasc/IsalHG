"""Unit tests for :mod:`isalhg.metric_space.metrics.information`.

Hand-computed values verify the fixed-width-code bits formula and the
incidence-list competitor model.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

from isalhg.metric_space.metrics.information import (
    alphabet_size_isalhg,
    bits_incidence_list,
    bits_isalhg,
    compression_ratio,
)


class TestAlphabetSize:
    def test_k2(self) -> None:
        # V_{1,1}: 1;  C_1,C_2: 2;  P_1,P_2: 2;  N_1,N_2: 2;  W: 1  → 8
        assert alphabet_size_isalhg(2) == 8

    def test_k3(self) -> None:
        # V pairs: (1,1),(1,2),(2,1) → 3;  C×3, P×3, N×3, W → 3+3+3+1=10 → total 13
        assert alphabet_size_isalhg(3) == 13

    def test_k10(self) -> None:
        # k*(k-1)//2 + 3k + 1 = 45 + 30 + 1 = 76
        assert alphabet_size_isalhg(10) == 76

    def test_monotone(self) -> None:
        sizes = [alphabet_size_isalhg(k) for k in range(2, 12)]
        assert all(sizes[i] < sizes[i + 1] for i in range(len(sizes) - 1))


class TestBitsIsalhg:
    def test_k2_length3(self) -> None:
        # |Σ(2)| = 8, |w| = 3 → 3 * log2(8) = 9.0
        result = bits_isalhg(3, k=2)
        assert abs(result - 9.0) < 1e-10

    def test_k3_length0(self) -> None:
        assert bits_isalhg(0, k=3) == 0.0

    def test_k2_length1(self) -> None:
        # 1 * log2(8) = 3.0
        assert abs(bits_isalhg(1, k=2) - 3.0) < 1e-10

    def test_proportional_to_length(self) -> None:
        b1 = bits_isalhg(5, k=4)
        b2 = bits_isalhg(10, k=4)
        assert abs(b2 - 2 * b1) < 1e-10


class TestBitsIncidenceList:
    def test_triangle_hand_computed(self) -> None:
        # n=3, 1 edge of arity 3
        # vertex bits: n-1 = 2
        # edge: 1 type bit + 3 * ceil(log2(3)) endpoint bits = 1 + 3*2 = 7
        # total = 2 + 7 = 9
        result = bits_incidence_list(n_nodes=3, arities=[3])
        assert abs(result - 9.0) < 1e-10

    def test_single_edge_arity2(self) -> None:
        # n=2, 1 edge of arity 2
        # vertex bits: 1
        # edge: 1 + 2*ceil(log2(2)) = 1 + 2*1 = 3
        # total = 1 + 3 = 4
        result = bits_incidence_list(n_nodes=2, arities=[2])
        assert abs(result - 4.0) < 1e-10

    def test_multiple_edges(self) -> None:
        # n=4, 2 edges of arity 2
        # vertex bits: 3
        # each edge: 1 + 2*ceil(log2(4)) = 1 + 2*2 = 5
        # total = 3 + 5 + 5 = 13
        result = bits_incidence_list(n_nodes=4, arities=[2, 2])
        assert abs(result - 13.0) < 1e-10

    def test_empty_edges(self) -> None:
        # n=1, no edges: vertex bits = 0
        result = bits_incidence_list(n_nodes=1, arities=[])
        assert result == 0.0


class TestCompressionRatio:
    def test_ratio_gt_one_when_comp_larger(self) -> None:
        r = compression_ratio(bits_comp=100.0, bits_isalhg_val=50.0)
        assert abs(r - 2.0) < 1e-10

    def test_ratio_one_when_equal(self) -> None:
        r = compression_ratio(bits_comp=80.0, bits_isalhg_val=80.0)
        assert abs(r - 1.0) < 1e-10

    def test_realistic_scenario(self) -> None:
        # Fano plane: n=7, 7 edges of arity 3, k=3
        # |w*| ~ 21 tokens (rough estimate for a 7-edge design)
        # B_IsalHG ~ 21 * log2(13) ≈ 21 * 3.7 ≈ 77.7 bits
        # B_comp = 6 (vertex) + 7*(1 + 3*ceil(log2(7))) = 6 + 7*(1+3*3) = 6+70 = 76 bits
        # ratio ≈ 76/77.7 ≈ 0.98 — not always > 1 for very small designs
        # This test just confirms no crash and ratio is positive
        n, arities = 7, [3] * 7
        b_comp = bits_incidence_list(n_nodes=n, arities=arities)
        b_isal = bits_isalhg(length=21, k=3)
        r = compression_ratio(b_comp, b_isal)
        assert r > 0.0
