"""``NautyLeviEditDistance`` -- the deliberate contrast baseline.

This representation maps each hypergraph ``H`` to the nauty canonical form of
its Levi bipartite graph ``B(H)``, then measures distance as the raw
Levenshtein edit distance between two such byte strings.  It is included in
the paper **not** as a competitive metric but as a *contrast*: because a
single structural edit can permute the entire nauty canonical labelling, the
resulting geometry is expected to be non-navigable (low HGED-correlation) and
cannot support application A4 (shortest path).  This is the scientific point
of the comparison; see ``docs/article/COMPETITORS.md`` §3.

Canonical-form construction
---------------------------
The fingerprint of ``H`` is

    ``fingerprint(H) = LeviGraph.color_signature() ++ bytes(pynauty.certificate(B(H)))``

where ``++`` denotes byte-string concatenation.  The Levi graph and its colour
colouring are built via ``isalhg.core.levi_reduction`` (stdlib-only); the
``pynauty`` binding computes the nauty canonical form.  The construction
mirrors ``isalhg.iso_backends.pynauty_levi.PynautyLeviBackend.fingerprint``
exactly, so ``fingerprint(H1) == fingerprint(H2)`` iff the two backends agree
on isomorphism.

Decision: color_signature is included inside the edit distance
--------------------------------------------------------------
T-TAe established that the ordered-partition colouring handed to nauty loses
absolute label identity: ``pynauty.certificate`` alone is not a complete
isomorphism invariant for labelled hypergraphs because two Levi graphs with
different colour-class sizes can share the same certificate.  The
``color_signature`` encodes the profile ``((colour, class_size), ...)`` in
20 bytes or fewer on a trivial-vocabulary corpus, restoring completeness.

Stripping the prefix and computing Levenshtein only over the certificate would
collapse any two non-isomorphic hypergraphs whose Levi graphs share the same
``(|V|, |E|)`` profile to distance 0, breaking the ``d == 0 iff iso``
property on labelled/mixed-order corpora and contradicting the fingerprint
stored in ``PynautyLeviBackend``.  On an unlabelled corpus the signature
contributes at most ``4 + 8 * n_color_classes`` bytes (≤ 20 for the common
trivial two-class case), so including it shifts D_est entries between
hypergraphs of different order by a bounded constant the paper acknowledges.

Imports
-------
``pynauty`` and ``rapidfuzz`` are imported inside method bodies so the module
loads without either dependency.  Missing imports raise
:class:`isalhg.errors.RepresentationDependencyMissingError` with install hints.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from isalhg.core.levi_reduction import LeviGraph, to_levi
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import RepresentationDependencyMissingError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.registry import register_distance
from isalhg.types import DistanceName

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def _import_pynauty() -> Any:
    try:
        import pynauty
    except ImportError as exc:
        raise RepresentationDependencyMissingError(
            "pynauty is required for NautyLeviEditDistance; install via `pip install pynauty`"
        ) from exc
    return pynauty


def _import_rapidfuzz() -> Any:
    try:
        from rapidfuzz.distance import Levenshtein
    except ImportError as exc:
        raise RepresentationDependencyMissingError(
            "rapidfuzz is required for NautyLeviEditDistance; install via `pip install rapidfuzz`"
        ) from exc
    return Levenshtein


def _build_pynauty_graph(levi: LeviGraph) -> Any:
    """Construct a ``pynauty.Graph`` from a ``LeviGraph`` with vertex colouring.

    Replicates the construction in
    ``isalhg.iso_backends.pynauty_levi._to_pynauty`` without importing
    ``iso_backends`` (which lies in a forbidden import direction for
    ``metric_space``).

    Parameters
    ----------
    levi : LeviGraph
        The Levi bipartite graph to encode.

    Returns
    -------
    pynauty.Graph
        Undirected graph ready for ``pynauty.certificate``.
    """
    pynauty = _import_pynauty()
    adjacency: dict[int, list[int]] = {node: [] for node in range(levi.n_nodes)}
    for u, v in levi.edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    return pynauty.Graph(
        number_of_vertices=levi.n_nodes,
        directed=False,
        adjacency_dict=adjacency,
        vertex_coloring=levi.color_classes(),
    )


def _fingerprint_levi(H: SparseHypergraph) -> bytes:
    """Return ``color_signature ++ pynauty_certificate`` for ``H``.

    Parameters
    ----------
    H : SparseHypergraph
        The hypergraph to fingerprint.

    Returns
    -------
    bytes
        Empty bytes for the empty hypergraph; otherwise the concatenation of
        ``LeviGraph.color_signature()`` and ``bytes(pynauty.certificate(...))``.
    """
    if H.n_nodes == 0:
        return b""
    pynauty = _import_pynauty()
    levi = to_levi(H)
    cert = pynauty.certificate(_build_pynauty_graph(levi))
    return levi.color_signature() + bytes(cert)


class NautyLeviEditDistance(HypergraphDistance):
    """Levenshtein distance between nauty canonical forms of Levi graphs.

    The fingerprint of ``H`` is ``LeviGraph.color_signature() ++
    bytes(pynauty.certificate(B(H)))``, matching
    :meth:`isalhg.iso_backends.pynauty_levi.PynautyLeviBackend.fingerprint`.
    The distance is the raw byte-level Levenshtein distance (rapidfuzz).

    This is the **contrast baseline** for the metric-space article: it is
    expected to produce a *non-navigable* geometry because one structural edit
    can permute the entire nauty canonical labelling.  Do not attempt to
    "improve" the geometry -- the poor correlation with HGED is the paper's
    scientific point.
    """

    @property
    def name(self) -> DistanceName:
        return "nauty_levi_edit"

    def fingerprint(self, H: SparseHypergraph) -> bytes:
        """Return the byte fingerprint ``color_signature ++ nauty_certificate``.

        Parameters
        ----------
        H : SparseHypergraph
            The hypergraph to encode.

        Returns
        -------
        bytes
            Byte string; length 0 for the empty hypergraph.

        Raises
        ------
        RepresentationDependencyMissingError
            If ``pynauty`` is not installed.
        """
        return _fingerprint_levi(H)

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        """Levenshtein distance between the byte fingerprints of ``H1`` and ``H2``.

        Parameters
        ----------
        H1, H2 : SparseHypergraph
            The two hypergraphs to compare.

        Returns
        -------
        float
            Non-negative integer cast to float; 0 iff the two fingerprints
            are identical (i.e. iff the Levi canonical forms agree, which
            implies isomorphism).

        Raises
        ------
        RepresentationDependencyMissingError
            If ``pynauty`` or ``rapidfuzz`` is not installed.
        """
        Levenshtein = _import_rapidfuzz()
        fp1 = _fingerprint_levi(H1)
        fp2 = _fingerprint_levi(H2)
        return float(Levenshtein.distance(fp1, fp2))

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        """Pairwise Levenshtein matrix over ``corpus``.

        Computes fingerprints once per hypergraph and then runs
        ``rapidfuzz.process.cdist`` for the full O(N^2) distance table.

        Parameters
        ----------
        corpus : Sequence[SparseHypergraph]
            Hypergraphs to compare; row/column ``i`` corresponds to
            ``corpus[i]``.

        Returns
        -------
        numpy.ndarray
            Symmetric ``(N, N)`` ``float64`` matrix with a zero diagonal.

        Raises
        ------
        RepresentationDependencyMissingError
            If ``pynauty``, ``rapidfuzz``, or ``numpy`` is not installed.
        """
        Levenshtein = _import_rapidfuzz()
        try:
            import numpy as np
            from rapidfuzz import process
        except ImportError as exc:
            raise RepresentationDependencyMissingError(
                "numpy and rapidfuzz are required for NautyLeviEditDistance.matrix(); "
                "install via `pip install numpy rapidfuzz`"
            ) from exc

        if not corpus:
            return np.zeros((0, 0), dtype=np.float64)

        fps = [_fingerprint_levi(H) for H in corpus]
        result = process.cdist(fps, fps, scorer=Levenshtein.distance, dtype=np.float64)
        return np.asarray(result, dtype=np.float64)


register_distance("nauty_levi_edit", lambda: NautyLeviEditDistance())
