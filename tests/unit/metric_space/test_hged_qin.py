"""Unit tests for :class:`isalhg.metric_space.distances.qin_hged.QinHGED`.

The Qin-faithful oracle is validated four ways: (1) against the paper's own
numeric anchors -- Example 2 (``HGED(EGO(u4), EGO(u5)) = 6``), Example 7's
optimal mapping cost decomposition, and the Definition 6 worked example;
(2) hand fixtures isolating the empty-shell taxonomy (deleting a ``k``-edge
costs ``k + 1``); (3) equality with the
exhaustive Algorithm 1+2 enumeration (``_dfs_reference``) on small random
pairs; (4) metric identities and the thresholded (Table II regime) semantics.
"""

from __future__ import annotations

import math
import random

import pytest

from isalhg.core.sparse_hypergraph import SparseHypergraph, ego_network, permute
from isalhg.errors import HGEDComputationError, VocabularyMismatchError
from isalhg.metric_space import registry
from isalhg.metric_space.distances.qin_hged import (
    QinHGED,
    _def6,
    _dfs_reference,
    _mapping_cost,
    _prepare,
)

pytestmark = pytest.mark.unit


def _qin(h1: SparseHypergraph, h2: SparseHypergraph) -> float:
    return QinHGED().pairwise(h1, h2)


class TestPaperAnchors:
    def test_example_2_hged_is_6(self, qin_fig1_hypergraph: SparseHypergraph) -> None:
        # HGED(EGO(u4), EGO(u5)) = 6 -- the one published numeric anchor.
        ego4 = ego_network(qin_fig1_hypergraph, 3)
        ego5 = ego_network(qin_fig1_hypergraph, 4)
        assert _qin(ego4, ego5) == 6.0

    def test_example_2_symmetric(self, qin_fig1_hypergraph: SparseHypergraph) -> None:
        ego4 = ego_network(qin_fig1_hypergraph, 3)
        ego5 = ego_network(qin_fig1_hypergraph, 4)
        assert _qin(ego5, ego4) == 6.0

    def test_def6_worked_example(self) -> None:
        # Paper p. 252: cards {5,4,3,2} vs {6,4,4,3} -> 1 + 0 + 1 + 1 = 3.
        assert _def6([5, 4, 3, 2], [6, 4, 4, 3]) == 3

    def test_example_7_optimal_mapping_costs_6(self, qin_fig1_hypergraph: SparseHypergraph) -> None:
        # The optimal correspondence of Example 7 (f''): node label cost 1
        # (u6 -> null) + edge label cost 2 (E1 orange->star, E2 -> null) +
        # incidence cost 3 (E2's members) = 6.
        ego4 = ego_network(qin_fig1_hypergraph, 3)  # nodes u1,u2,u4,u5,u6,u7,u8 -> 0..6
        ego5 = ego_network(qin_fig1_hypergraph, 4)  # nodes u2,u3,u4,u5,u7,u8 -> 0..5
        pair = _prepare(ego4, ego5)
        # _prepare keeps ego4 as source (7 >= 6 nodes). Source ids: u1=0, u2=1,
        # u4=2, u5=3, u6=4, u7=5, u8=6; target ids: u2=0, u3=1, u4=2, u5=3,
        # u7=4, u8=5. f'': u1->u3, u2->u2, u4->u5, u5->u4, u6->null, u7->u7,
        # u8->u8; E1->E3, E2->null, E4->E4 (source edges ordered E1,E2,E4 by
        # construction; source edge ids follow ego4's iter order).
        node_map = [1, 0, 3, 2, -1, 4, 5]
        # ego4 edges in id order: E1={0,1,2}, E2={2,4,5}, E4={2,3,5,6};
        # ego5 edges: E3={0,1,3} id 0, E4={2,3,4,5} id 1.
        edge_map = [0, -1, 1]
        assert _mapping_cost(pair, node_map, edge_map) == 6


class TestEmptyShellTaxonomy:
    def test_delete_k_edge_costs_k_plus_1(self) -> None:
        # Qin's empty-shell convention: 3 incidence reduces + 1 shell delete = 4.
        h1 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        h2 = SparseHypergraph(3, [])
        assert _qin(h1, h2) == 4.0

    def test_insert_k_edge_costs_k_plus_1(self) -> None:
        h1 = SparseHypergraph(3, [])
        h2 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        assert _qin(h1, h2) == 4.0

    def test_delete_degree_h_vertex_costs_h_plus_1(self) -> None:
        # Vertex 3 sits in two edges and both survive it: 2 incidence reduces
        # + 1 isolated delete = 3 (Def 5 + Def 6 confirm 3 is a lower bound).
        h1 = SparseHypergraph(4, [frozenset({0, 1, 3}), frozenset({1, 2, 3})])
        h2 = SparseHypergraph(3, [frozenset({0, 1}), frozenset({1, 2})])
        assert _qin(h1, h2) == 3.0

    def test_insert_isolated_vertex(self) -> None:
        h1 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        h2 = SparseHypergraph(4, [frozenset({0, 1, 2})])
        assert _qin(h1, h2) == 1.0

    def test_single_incidence_extend(self) -> None:
        h1 = SparseHypergraph(3, [frozenset({0, 1})])
        h2 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        assert _qin(h1, h2) == 1.0

    def test_vertex_label_substitution(self) -> None:
        h1 = SparseHypergraph(2, [frozenset({0, 1})], n_vertex_labels=2, vertex_labels=[0, 0])
        h2 = SparseHypergraph(2, [frozenset({0, 1})], n_vertex_labels=2, vertex_labels=[0, 1])
        assert _qin(h1, h2) == 1.0

    def test_edge_label_substitution(self) -> None:
        h1 = SparseHypergraph(2, [frozenset({0, 1})], n_edge_labels=2, edge_labels=[0])
        h2 = SparseHypergraph(2, [frozenset({0, 1})], n_edge_labels=2, edge_labels=[1])
        assert _qin(h1, h2) == 1.0


class TestMetricIdentities:
    def test_self_distance_zero(self, fano_plane: SparseHypergraph) -> None:
        assert _qin(fano_plane, fano_plane) == 0.0

    def test_permutation_invariance_is_zero(self) -> None:
        h = SparseHypergraph(5, [frozenset({0, 1, 2}), frozenset({2, 3}), frozenset({3, 4})])
        assert _qin(h, permute(h, [4, 3, 2, 1, 0])) == 0.0

    def test_symmetry(self) -> None:
        h1 = SparseHypergraph(4, [frozenset({0, 1, 2}), frozenset({2, 3})])
        h2 = SparseHypergraph(3, [frozenset({0, 1})])
        assert _qin(h1, h2) == _qin(h2, h1)

    def test_positive_on_non_iso(
        self, non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph]
    ) -> None:
        h1, h2 = non_iso_pair_small
        assert _qin(h1, h2) > 0.0

    def test_vocab_mismatch_raises(self) -> None:
        h1 = SparseHypergraph(2, [frozenset({0, 1})], n_vertex_labels=2)
        h2 = SparseHypergraph(2, [frozenset({0, 1})])
        with pytest.raises(VocabularyMismatchError):
            _qin(h1, h2)


class TestAgainstDFSReference:
    def test_bfs_equals_exhaustive_on_random_tiny_pairs(self) -> None:
        rng = random.Random(0)
        for trial in range(30):
            n1, n2 = rng.randint(1, 4), rng.randint(1, 4)
            m1, m2 = rng.randint(0, 3), rng.randint(0, 3)

            def rand_h(n: int, m: int) -> SparseHypergraph:
                edges: list[frozenset[int]] = []
                labels: list[int] = []
                tries = 0
                while len(edges) < m and tries < 30:
                    tries += 1
                    size = rng.randint(1, n)
                    members = frozenset(rng.sample(range(n), size))
                    label = rng.randrange(2)
                    if (label, members) not in zip(labels, edges, strict=True):
                        edges.append(members)
                        labels.append(label)
                return SparseHypergraph(
                    n,
                    edges,
                    n_vertex_labels=2,
                    n_edge_labels=2,
                    vertex_labels=[rng.randrange(2) for _ in range(n)],
                    edge_labels=labels,
                )

            h1, h2 = rand_h(n1, m1), rand_h(n2, m2)
            expected = _dfs_reference(h1, h2)
            assert _qin(h1, h2) == float(expected), f"trial {trial}: {h1!r} vs {h2!r}"


class TestThresholdedMode:
    def test_clamp_below_true_value_returns_inf(self) -> None:
        # True Qin HGED is 4 (delete the 3-edge); clamp 3 proves "> 3" only.
        h1 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        h2 = SparseHypergraph(3, [])
        assert QinHGED(upper_bound=3).pairwise(h1, h2) == math.inf

    def test_clamp_at_true_value_returns_exact(self) -> None:
        h1 = SparseHypergraph(3, [frozenset({0, 1, 2})])
        h2 = SparseHypergraph(3, [])
        assert QinHGED(upper_bound=4).pairwise(h1, h2) == 4.0

    def test_max_expansions_raises(self) -> None:
        h1 = SparseHypergraph(4, [frozenset({0, 1}), frozenset({2, 3})])
        h2 = SparseHypergraph(4, [frozenset({0, 1}), frozenset({1, 2})])
        with pytest.raises(HGEDComputationError):
            QinHGED(max_expansions=1).pairwise(h1, h2)


class TestOracleSolverAgreement:
    def test_bnb_oracle_matches_bfs_on_example_2(
        self, qin_fig1_hypergraph: SparseHypergraph
    ) -> None:
        # Same official metric, two independent solvers: both must return 6.
        pytest.importorskip("scipy")
        pytest.importorskip("numpy")
        from isalhg.metric_space.distances.hged import ExactHGED

        ego4 = ego_network(qin_fig1_hypergraph, 3)
        ego5 = ego_network(qin_fig1_hypergraph, 4)
        assert ExactHGED().pairwise(ego4, ego5) == 6.0
        assert _qin(ego4, ego5) == 6.0


class TestRegistry:
    def test_registered_and_retrievable(self) -> None:
        d = registry.get_distance("qin_hged")
        assert isinstance(d, QinHGED)
        assert d.name == "qin_hged"
        assert "qin_hged" in registry.available_distances()
