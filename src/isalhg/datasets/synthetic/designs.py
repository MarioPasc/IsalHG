"""Hand-built symmetric designs -- the single source of truth.

These four structures are the torture-test fixtures of the whole codebase: they
are the only small hypergraphs with large, known automorphism groups, so they
exercise the tie-breaking cascade of the canonical algorithm in a way random
instances never do. Every consumer -- ``tests/conftest.py``, the registered
datasets in this package, and the benchmark scripts -- builds them from here.

The builders are pure functions of no arguments (or of an explicit base block),
import only :mod:`isalhg.core.sparse_hypergraph`, and register nothing, so this
module is safe to import from anywhere.

``gq_2_2_doily`` is *constructed*, not transcribed. A hardcoded edge list for it
shipped until T-M0a and turned out to have two lines meeting in two points --
a partial-linear-space violation that destroyed the vertex-transitivity every
caller assumed. ``tests/unit/datasets/test_designs.py`` asserts the defining
incidence axioms rather than the resulting edge lists.

Citations
---------
- Fano plane PG(2, 2): Beth, Jungnickel & Lenz, *Design Theory*, 1999.
- STS(9) as AG(2, 3): Hall, *Combinatorial Theory*, 1986.
- STS(13) classification (exactly two iso-classes): Heinlein 2023,
  arXiv:2303.01207. It does *not* certify ``cyclic_sts_13``, which is a
  single-orbit partial system -- see that function.
- GQ(2, 2) as the duad-syntheme geometry of ``S_6``: Sylvester 1861; Payne &
  Thas, *Finite Generalized Quadrangles*, §1.2 (the symplectic W(2) model is
  isomorphic to it).
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator

from isalhg.core.sparse_hypergraph import SparseHypergraph


def fano_plane() -> SparseHypergraph:
    """Fano plane STS(7): the lines of PG(2, 2).

    Returns
    -------
    SparseHypergraph
        7 points, 7 lines, 3-uniform. Every pair of points lies on exactly one
        line; ``Aut = PGL(3, 2)`` of order 168, vertex-transitive.
    """
    lines = [
        frozenset({0, 1, 2}),
        frozenset({0, 3, 4}),
        frozenset({0, 5, 6}),
        frozenset({1, 3, 5}),
        frozenset({1, 4, 6}),
        frozenset({2, 3, 6}),
        frozenset({2, 4, 5}),
    ]
    return SparseHypergraph(n_nodes=7, hyperedges=lines)


def sts_9() -> SparseHypergraph:
    """The unique Steiner triple system STS(9), realised as AG(2, 3).

    Returns
    -------
    SparseHypergraph
        9 points on a 3x3 affine plane, 12 blocks (three rows, three columns,
        and the two diagonal parallel classes), 3-uniform.
    """
    blocks = [
        frozenset({0, 1, 2}),
        frozenset({3, 4, 5}),
        frozenset({6, 7, 8}),
        frozenset({0, 3, 6}),
        frozenset({1, 4, 7}),
        frozenset({2, 5, 8}),
        frozenset({0, 4, 8}),
        frozenset({1, 5, 6}),
        frozenset({2, 3, 7}),
        frozenset({0, 5, 7}),
        frozenset({1, 3, 8}),
        frozenset({2, 4, 6}),
    ]
    return SparseHypergraph(n_nodes=9, hyperedges=blocks)


def cyclic_sts_13(base: tuple[int, int, int]) -> SparseHypergraph:
    """One cyclic orbit of triples on ``Z/13Z``.

    Despite the name -- kept because every caller and the archived empirical
    results use it -- this is **not** a Steiner triple system. A single starter
    block generates 13 blocks covering 39 of the 78 point-pairs; STS(13) needs
    26 blocks from two starters (e.g. ``(0, 1, 4)`` together with ``(0, 2, 7)``).
    What callers actually rely on is that the result is 3-uniform, 3-regular and
    vertex-transitive under the rotation action, all of which hold.

    Parameters
    ----------
    base : tuple[int, int, int]
        Starter block. ``(0, 1, 4)`` and ``(0, 1, 6)`` generate the
        non-isomorphic pair used as the hard negative for the iso backends.

    Returns
    -------
    SparseHypergraph
        13 points, 13 blocks -- the rotates ``{(b + i) mod 13 : b in base}``.
    """
    n = 13
    blocks = [frozenset((b + i) % n for b in base) for i in range(n)]
    return SparseHypergraph(n_nodes=n, hyperedges=blocks)


def _synthemes(elements: tuple[int, ...]) -> Iterator[tuple[tuple[int, int], ...]]:
    """Yield every perfect matching of ``elements`` as a tuple of pairs.

    ``elements`` is kept in ascending order by the recursion, so ``first`` is
    always the least remaining element and every emitted pair is ascending.
    """
    if not elements:
        yield ()
        return
    first, rest = elements[0], elements[1:]
    for i, partner in enumerate(rest):
        for tail in _synthemes(rest[:i] + rest[i + 1 :]):
            yield ((first, partner),) + tail


def gq_2_2_doily() -> SparseHypergraph:
    """Generalised quadrangle GQ(2, 2), the "doily".

    Built as Sylvester's duad-syntheme geometry of the symmetric group ``S_6``:
    the 15 points are the *duads* (2-subsets of ``{1..6}``, indexed in
    ``itertools.combinations`` order) and the 15 lines are the *synthemes*
    (perfect matchings of ``{1..6}``, each a set of three pairwise-disjoint
    duads). This is isomorphic to the symplectic realisation W(2) over GF(2).

    Returns
    -------
    SparseHypergraph
        15 points, 15 lines, 3-uniform; every point on 3 lines; two lines meet
        in at most one point. The collinearity graph is the Kneser graph
        ``K(6, 2)``, strongly regular with parameters ``(15, 6, 1, 3)``.
        ``Aut = S_6`` of order 720, acting transitively on the points.
    """
    duads = list(itertools.combinations(range(1, 7), 2))
    duad_id = {duad: i for i, duad in enumerate(duads)}
    lines = [
        frozenset(duad_id[pair] for pair in syntheme) for syntheme in _synthemes(tuple(range(1, 7)))
    ]
    return SparseHypergraph(n_nodes=len(duads), hyperedges=lines)
