"""Unit tests for the canonical address map and the two nauty tokenizations."""

from __future__ import annotations

import random

import pytest

from isalhg.core.fact_word import encode_fact_word
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.iso_backends.canonical_order import (
    canonical_ranks,
    nauty_certificate_bytes,
    nauty_certificate_rows,
)
from isalhg.iso_backends.pynauty_levi import PynautyLeviBackend

pytestmark = pytest.mark.unit

pynauty = pytest.importorskip("pynauty")


def random_kb(rng: random.Random, *, n_max: int = 8, n_types: int = 2, n_preds: int = 2):
    """A small labelled knowledge base; small so isomorphic duplicates occur."""
    n = rng.randint(3, n_max)
    m = rng.randint(2, 6)
    seen: set[tuple[int, frozenset[int]]] = set()
    edges: list[set[int]] = []
    labels: list[int] = []
    for _ in range(m * 4):
        if len(edges) == m:
            break
        arity = rng.randint(2, min(4, n))
        members = frozenset(rng.sample(range(n), arity))
        label = rng.randrange(n_preds)
        if (label, members) in seen:
            continue
        seen.add((label, members))
        edges.append(set(members))
        labels.append(label)
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=edges,
        n_vertex_labels=n_types,
        n_edge_labels=n_preds,
        vertex_labels=[rng.randrange(n_types) for _ in range(n)],
        edge_labels=labels,
    )


class TestCanonicalRanks:
    def test_is_a_permutation(self, fano_plane: SparseHypergraph) -> None:
        rank = canonical_ranks(fano_plane)
        assert sorted(rank) == list(range(fano_plane.n_nodes))

    def test_empty_hypergraph(self) -> None:
        assert canonical_ranks(SparseHypergraph(n_nodes=0, hyperedges=[])) == ()

    def test_single_constant(self) -> None:
        assert canonical_ranks(SparseHypergraph(n_nodes=1, hyperedges=[])) == (0,)

    def test_deterministic(self, sts_9: SparseHypergraph) -> None:
        assert canonical_ranks(sts_9) == canonical_ranks(sts_9)

    def test_equivariant_when_the_levi_graph_is_rigid(self) -> None:
        """With a trivial automorphism group the rank vector is equivariant outright."""
        rng = random.Random(3)
        checked = 0
        for _ in range(1200):
            H = random_kb(rng)
            if _levi_automorphism_count(H) != 1:
                continue
            sigma = list(range(H.n_nodes))
            rng.shuffle(sigma)
            r1 = canonical_ranks(H)
            r2 = canonical_ranks(permute(H, sigma))
            assert all(r2[sigma[v]] == r1[v] for v in range(H.n_nodes)), (
                f"rigid instance broke equivariance: {r1} vs {r2} under {sigma}"
            )
            checked += 1
        assert checked >= 20, f"only {checked} rigid instances sampled"

    def test_rank_vector_alone_is_not_equivariant(self) -> None:
        """The negative control for the docstring's claim.

        A canonical labelling pins the canonical *form*, not the permutation
        reaching it: two isomorphic inputs may be labelled by permutations
        differing by an automorphism. The rank vector is therefore not a
        transportable address; only the induced word is.
        """
        rng = random.Random(7)
        mismatches = 0
        for _ in range(400):
            H = random_kb(rng)
            sigma = list(range(H.n_nodes))
            rng.shuffle(sigma)
            r1 = canonical_ranks(H)
            r2 = canonical_ranks(permute(H, sigma))
            if not all(r2[sigma[v]] == r1[v] for v in range(H.n_nodes)):
                mismatches += 1
        assert mismatches > 0

    def test_the_induced_word_is_invariant(self) -> None:
        """What the article actually rests on, and what the mismatch above does not touch."""
        rng = random.Random(7)
        for _ in range(400):
            H = random_kb(rng)
            sigma = list(range(H.n_nodes))
            rng.shuffle(sigma)
            H2 = permute(H, sigma)
            assert encode_fact_word(H, canonical_ranks(H)) == encode_fact_word(
                H2, canonical_ranks(H2)
            )


def _levi_automorphism_count(H: SparseHypergraph) -> int:
    """Return ``|Aut|`` of the coloured Levi graph of ``H``."""
    from isalhg.core.levi_reduction import to_levi
    from isalhg.iso_backends.canonical_order import _to_pynauty

    _, size1, size2, _, _ = pynauty.autgrp(_to_pynauty(to_levi(H)))
    return round(size1 * 10**size2)


class TestCertificateBytes:
    def test_matches_the_pynauty_backend_fingerprint(self, sts_9: SparseHypergraph) -> None:
        assert nauty_certificate_bytes(sts_9) == PynautyLeviBackend().fingerprint(sts_9)

    def test_empty_hypergraph(self) -> None:
        assert nauty_certificate_bytes(SparseHypergraph(n_nodes=0, hyperedges=[])) == b""

    def test_agrees_with_the_backend_on_random_inputs(self) -> None:
        rng = random.Random(11)
        backend = PynautyLeviBackend()
        for _ in range(60):
            H = random_kb(rng)
            assert nauty_certificate_bytes(H) == backend.fingerprint(H)


class TestCertificateRows:
    def test_one_row_per_levi_node(self, fano_plane: SparseHypergraph) -> None:
        rows = nauty_certificate_rows(fano_plane)
        assert len(rows) == fano_plane.n_nodes + fano_plane.n_edges

    def test_empty_hypergraph(self) -> None:
        assert nauty_certificate_rows(SparseHypergraph(n_nodes=0, hyperedges=[])) == ()

    def test_rows_are_symmetric_and_carry_the_colour_first(
        self, fano_plane: SparseHypergraph
    ) -> None:
        rows = nauty_certificate_rows(fano_plane)
        # Constant nodes sit in colour 0, fact nodes in colour |Sigma_V| = 1.
        assert sorted(row[0] for row in rows) == [0] * 7 + [1] * 7
        # Adjacency is symmetric: j in row i iff i in row j.
        for i, row in enumerate(rows):
            for j in row[1:]:
                assert i in rows[j][1:]

    def test_equal_for_isomorphic_and_different_for_non_isomorphic(
        self,
        iso_pair_small: tuple[SparseHypergraph, SparseHypergraph, list[int]],
        non_iso_pair_small: tuple[SparseHypergraph, SparseHypergraph],
    ) -> None:
        H1, H2, _ = iso_pair_small
        assert nauty_certificate_rows(H1) == nauty_certificate_rows(H2)
        A, B = non_iso_pair_small
        assert nauty_certificate_rows(A) != nauty_certificate_rows(B)

    def test_colour_in_the_row_separates_relabelled_copies(self) -> None:
        """Without the colour these two would share their adjacency rows."""
        edges = [{0, 1}, {1, 2}]
        base = {"n_nodes": 3, "hyperedges": edges, "n_vertex_labels": 2, "n_edge_labels": 1}
        A = SparseHypergraph(**base, vertex_labels=[0, 0, 0], edge_labels=[0, 0])
        B = SparseHypergraph(**base, vertex_labels=[1, 1, 1], edge_labels=[0, 0])
        assert PynautyLeviBackend().fingerprint(A) != PynautyLeviBackend().fingerprint(B)
        assert nauty_certificate_rows(A) != nauty_certificate_rows(B)

    def test_partition_agrees_with_the_pynauty_fingerprint(self) -> None:
        """Rows merge exactly the knowledge bases nauty calls isomorphic."""
        rng = random.Random(13)
        backend = PynautyLeviBackend()
        corpus = [random_kb(rng, n_max=5) for _ in range(200)]
        by_rows: dict[object, set[bytes]] = {}
        for H in corpus:
            by_rows.setdefault(nauty_certificate_rows(H), set()).add(backend.fingerprint(H))
        collisions = sum(1 for group in by_rows.values() if len(group) > 1)
        assert collisions == 0
        # And the reverse direction: one row sequence per fingerprint.
        by_cert: dict[bytes, set[object]] = {}
        for H in corpus:
            by_cert.setdefault(backend.fingerprint(H), set()).add(nauty_certificate_rows(H))
        assert all(len(group) == 1 for group in by_cert.values())
        # The corpus really does contain repeated isomorphism classes.
        assert len(by_cert) < len(corpus)
