"""Query x catalogue distance rectangles for Design D (LOG.md §7).

Each arm's rectangle is, by construction, the ``[queries, catalogue]`` block of
the arm's own ``matrix()`` over the corpus ``catalogue + queries`` (catalogue
first). That pins the two things that could otherwise drift from the cached
campaign matrices:

* the per-pair value: every fingerprint arm reuses the library's fingerprint and
  the library's pair function (Levenshtein over the same symbols, L2 over the
  same NetLSD signature, JSD over the same portrait, padded L1, size L1);
* the orientation of the non-symmetric pairwise arms (the bipartite GED): the
  library's ``matrix`` evaluates ``pairwise(items[i], items[j])`` with ``i < j``
  and mirrors it, so with the catalogue first a query-catalogue entry is
  ``pairwise(catalogue_record, query)``.

The two WL arms are corpus-level by definition (one WL run on the disjoint
union), so their rectangle is read off one WL run over ``catalogue + queries``;
the one-round arm is insensitive to the union, the registry arm is not (it
refines to the union's stable partition) and is footnoted as degenerate.

Catalogue fingerprints are computed once per job (:meth:`ArmRect.fit`) and
reused for every seed and ``r``; the bipartite arms are parallelised over
query blocks with joblib (fork-based multiprocessing backend, so the catalogue
is inherited, not pickled).
"""

from __future__ import annotations

import math
import time
from collections import Counter
from collections.abc import Hashable, Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

from isalhg.core.sparse_hypergraph import SparseHypergraph

FloatMatrix = NDArray[np.float64]

_STATE: dict[str, Any] = {}


class RectError(Exception):
    """A rectangle cannot be computed as requested."""


class ArmRect:
    """Distances from queries to a fixed catalogue under one arm.

    Parameters
    ----------
    name : str
        Arm name (registry name, or ``wl_h1``).
    n_jobs : int, optional
        Worker processes for the pairwise arms.
    """

    def __init__(self, name: str, n_jobs: int = 1) -> None:
        self.name = name
        self.n_jobs = max(1, int(n_jobs))
        self.catalogue: list[SparseHypergraph] = []
        self._fp: list[Any] = []
        self.secs_fit = 0.0
        self.last_pairs_per_s: float | None = None

    # ------------------------------------------------------------------ hooks

    def fingerprint(self, H: SparseHypergraph) -> Any:  # noqa: ANN401 - per-arm object
        """The per-record object the pair function consumes."""
        return None

    def pair_block(self, q_fps: list[Any], c_fps: list[Any]) -> FloatMatrix:
        """``(len(q_fps), len(c_fps))`` distances from fingerprints."""
        raise NotImplementedError

    # ------------------------------------------------------------------ API

    def fit(self, catalogue: Sequence[SparseHypergraph]) -> ArmRect:
        """Cache the catalogue and its fingerprints."""
        t0 = time.perf_counter()
        self.catalogue = list(catalogue)
        self._fp = self._fingerprints(self.catalogue)
        self.secs_fit = time.perf_counter() - t0
        return self

    def _fingerprints(self, hs: Sequence[SparseHypergraph]) -> list[Any]:
        return [self.fingerprint(H) for H in hs]

    def rect(self, queries: Sequence[SparseHypergraph]) -> FloatMatrix:
        """``(len(queries), len(catalogue))`` distances."""
        return self.pair_block(self._fingerprints(queries), self._fp)


# --------------------------------------------------------------------------- Levenshtein arms


class _SymbolEncoder:
    """One growing symbol -> code-point map, shared by the catalogue and every query batch.

    Levenshtein is invariant under any bijective relabelling of symbols, so a shared
    map gives exactly the distances of the library's per-corpus ``_encode``.
    """

    def __init__(self) -> None:
        self.vocab: dict[Hashable, str] = {}

    def __call__(self, seq: Sequence[Hashable]) -> str:
        out = []
        for sym in seq:
            ch = self.vocab.get(sym)
            if ch is None:
                ch = chr(0x100 + len(self.vocab))
                self.vocab[sym] = ch
            out.append(ch)
        return "".join(out)


class LevenshteinArm(ArmRect):
    """Token Levenshtein over a per-record symbol sequence (word, fact list, cert rows/bytes)."""

    def __init__(self, name: str, n_jobs: int = 1) -> None:
        super().__init__(name, n_jobs)
        self._enc = _SymbolEncoder()
        if name == "isal_ow_struct":
            from isalhg.metric_space.distances.isal_ordered import IsalOrderedLevenshtein

            self._fpfun = IsalOrderedLevenshtein().fingerprint
        elif name == "fact_rank":
            from isalhg.metric_space.distances.fact_levenshtein import fact_word

            self._fpfun = fact_word
        elif name == "nauty_cert_rows":
            from isalhg.metric_space.representations.nauty_levi_edit import NautyCertRowsDistance

            self._fpfun = NautyCertRowsDistance().fingerprint
        elif name == "nauty_cert":
            from isalhg.metric_space.representations.nauty_levi_edit import NautyLeviEditDistance

            self._fpfun = NautyLeviEditDistance().fingerprint
        else:
            raise RectError(f"{name} is not a Levenshtein arm")

    def fingerprint(self, H: SparseHypergraph) -> str:
        fp = self._fpfun(H)
        # The certificate is compared byte by byte; bytes iterate as ints, one symbol each.
        return self._enc(tuple(fp))

    def pair_block(self, q_fps: list[Any], c_fps: list[Any]) -> FloatMatrix:
        from rapidfuzz import process
        from rapidfuzz.distance import Levenshtein

        if not q_fps or not c_fps:
            return np.zeros((len(q_fps), len(c_fps)))
        out = process.cdist(
            q_fps, c_fps, scorer=Levenshtein.distance, dtype=np.float64, workers=self.n_jobs
        )
        return np.asarray(out, dtype=np.float64)


# --------------------------------------------------------------------------- vector arms


class NetLSDArm(ArmRect):
    """L2 between NetLSD heat-trace signatures."""

    def __init__(self, name: str = "netlsd", n_jobs: int = 1) -> None:
        super().__init__(name, n_jobs)
        from isalhg.metric_space.representations.netlsd import NetLSDDistance

        self._d = NetLSDDistance()

    def _fingerprints(self, hs: Sequence[SparseHypergraph]) -> list[Any]:
        return _parallel_map(self._d.fingerprint, hs, self.n_jobs)

    def pair_block(self, q_fps: list[Any], c_fps: list[Any]) -> FloatMatrix:
        C = np.vstack(c_fps)
        out = np.empty((len(q_fps), len(c_fps)))
        for i, q in enumerate(q_fps):
            out[i] = np.linalg.norm(C - q[None, :], axis=1)
        return out


class HPDArm(ArmRect):
    """sqrt(JSD) between hyperedge portraits (the vendored HPD)."""

    def __init__(self, name: str = "hpd_jsd", n_jobs: int = 1) -> None:
        super().__init__(name, n_jobs)

    @staticmethod
    def _portrait(H: SparseHypergraph) -> Any:  # noqa: ANN401 - vendored portrait object
        from isalhg.adapters.xgi_adapter import XGIAdapter
        from isalhg.metric_space.representations import _hpd_vendor

        return _hpd_vendor.hyperedge_portrait(XGIAdapter().to_external(H))

    def _fingerprints(self, hs: Sequence[SparseHypergraph]) -> list[Any]:
        return _parallel_map(HPDArm._portrait, hs, self.n_jobs)

    def pair_block(self, q_fps: list[Any], c_fps: list[Any]) -> FloatMatrix:
        _STATE["hpd"] = (q_fps, c_fps)
        rows = _parallel_rows(_hpd_rows, len(q_fps), self.n_jobs)
        _STATE.pop("hpd", None)
        return np.vstack(rows) if rows else np.zeros((0, len(c_fps)))


def _hpd_rows(lo: int, hi: int) -> FloatMatrix:
    from isalhg.metric_space.representations import _hpd_vendor

    q_fps, c_fps = _STATE["hpd"]
    out = np.empty((hi - lo, len(c_fps)))
    for i in range(lo, hi):
        for j, c in enumerate(c_fps):
            # catalogue first, as in the library's matrix over ``catalogue + queries``
            out[i - lo, j] = math.sqrt(_hpd_vendor.hyper_portrait_divergence(c, q_fps[i]))
    return out


class DegreeArm(ArmRect):
    """Zero-padded L1 between descending degree sequences."""

    def fingerprint(self, H: SparseHypergraph) -> NDArray[np.int64]:
        return np.array(sorted((H.degree(v) for v in range(H.n_nodes)), reverse=True))

    def pair_block(self, q_fps: list[Any], c_fps: list[Any]) -> FloatMatrix:
        width = max(len(x) for x in [*q_fps, *c_fps])
        Q = np.vstack([np.pad(x, (0, width - len(x))) for x in q_fps])
        C = np.vstack([np.pad(x, (0, width - len(x))) for x in c_fps])
        return np.vstack([np.abs(C - q[None, :]).sum(axis=1) for q in Q]).astype(np.float64)


class SizeArm(ArmRect):
    """``|n1 - n2| + |m1 - m2|``."""

    def fingerprint(self, H: SparseHypergraph) -> tuple[int, int]:
        return (H.n_nodes, H.n_edges)

    def pair_block(self, q_fps: list[Any], c_fps: list[Any]) -> FloatMatrix:
        Q = np.array(q_fps, dtype=np.float64)
        C = np.array(c_fps, dtype=np.float64)
        return np.abs(Q[:, None, 0] - C[None, :, 0]) + np.abs(Q[:, None, 1] - C[None, :, 1])


# --------------------------------------------------------------------------- WL arms


class WLArm(ArmRect):
    """WL colour-histogram L1, one WL run over ``catalogue + queries`` (the library's union)."""

    def __init__(self, name: str, n_jobs: int = 1, max_rounds: int | None = None) -> None:
        super().__init__(name, n_jobs)
        from isalhg.metric_space.representations.wl import HypergraphWLDistance

        self._d = HypergraphWLDistance(metric="l1", max_rounds=max_rounds)

    def fit(self, catalogue: Sequence[SparseHypergraph]) -> ArmRect:
        self.catalogue = list(catalogue)
        return self

    def rect(self, queries: Sequence[SparseHypergraph]) -> FloatMatrix:
        hist = self._d._histograms([*self.catalogue, *queries])
        cat, qs = hist[: len(self.catalogue)], hist[len(self.catalogue) :]
        out = np.empty((len(qs), len(cat)))
        for i, h in enumerate(qs):
            for j, g in enumerate(cat):
                out[i, j] = _l1_counter(h, g)
        return out


def _l1_counter(a: Counter[int], b: Counter[int]) -> float:
    return float(sum(abs(a.get(k, 0) - b.get(k, 0)) for k in a.keys() | b.keys()))


# --------------------------------------------------------------------------- pairwise arms


class PairwiseArm(ArmRect):
    """The library's ``pairwise`` on every (catalogue record, query) pair, in that order."""

    def __init__(self, name: str, n_jobs: int = 1) -> None:
        super().__init__(name, n_jobs)
        from isalhg.metric_space.registry import get_distance

        self._d = get_distance(name)

    def fit(self, catalogue: Sequence[SparseHypergraph]) -> ArmRect:
        self.catalogue = list(catalogue)
        return self

    def rect(self, queries: Sequence[SparseHypergraph]) -> FloatMatrix:
        t0 = time.perf_counter()
        _STATE["pair"] = (self._d, list(queries), self.catalogue)
        rows = _parallel_rows(_pair_rows, len(queries), self.n_jobs)
        _STATE.pop("pair", None)
        dt = time.perf_counter() - t0
        n_pairs = len(queries) * len(self.catalogue)
        self.last_pairs_per_s = n_pairs / dt if dt > 0 else None
        return np.vstack(rows) if rows else np.zeros((0, len(self.catalogue)))


def _pair_rows(lo: int, hi: int) -> FloatMatrix:
    d, queries, catalogue = _STATE["pair"]
    out = np.empty((hi - lo, len(catalogue)))
    for i in range(lo, hi):
        q = queries[i]
        for j, c in enumerate(catalogue):
            out[i - lo, j] = float(d.pairwise(c, q))
    return out


# --------------------------------------------------------------------------- parallel helpers


def _parallel_rows(fn: Any, n: int, n_jobs: int) -> list[FloatMatrix]:  # noqa: ANN401
    """Apply ``fn(lo, hi)`` over row blocks; fork-based joblib so ``_STATE`` is inherited."""
    if n == 0:
        return []
    if n_jobs <= 1:
        return [fn(0, n)]
    from joblib import Parallel, delayed

    step = max(1, math.ceil(n / (n_jobs * 4)))
    bounds = [(lo, min(n, lo + step)) for lo in range(0, n, step)]
    return list(
        Parallel(n_jobs=n_jobs, backend="multiprocessing")(delayed(fn)(a, b) for a, b in bounds)
    )


def _map_block(lo: int, hi: int) -> list[Any]:
    fn, items = _STATE["map"]
    return [fn(x) for x in items[lo:hi]]


def _parallel_map(fn: Any, items: Sequence[Any], n_jobs: int) -> list[Any]:  # noqa: ANN401
    """``[fn(x) for x in items]`` over fork-based joblib workers, order preserved."""
    if n_jobs <= 1 or len(items) < 2 * n_jobs:
        return [fn(x) for x in items]
    _STATE["map"] = (fn, list(items))
    try:
        blocks = _parallel_rows(_map_block, len(items), n_jobs)
    finally:
        _STATE.pop("map", None)
    return [x for block in blocks for x in block]


# --------------------------------------------------------------------------- factory


def make_arm(name: str, n_jobs: int = 1) -> ArmRect:
    """The rectangle implementation of ``name``.

    Raises
    ------
    RectError
        For an arm with no rectangle implementation (``wstar_orbit``).
    """
    if name in ("isal_ow_struct", "fact_rank", "nauty_cert_rows", "nauty_cert"):
        return LevenshteinArm(name, n_jobs)
    if name == "netlsd":
        return NetLSDArm(name, n_jobs)
    if name == "hpd_jsd":
        return HPDArm(name, n_jobs)
    if name == "degree_seq_l1":
        return DegreeArm(name, n_jobs)
    if name == "size_l1":
        return SizeArm(name, n_jobs)
    if name == "wl_h1":
        return WLArm(name, n_jobs, max_rounds=1)
    if name == "wl_l1":
        return WLArm(name, n_jobs, max_rounds=None)
    if name in ("bipartite_ged_assign", "bipartite_ged_path"):
        return PairwiseArm(name, n_jobs)
    raise RectError(f"no rectangle implementation for arm {name!r}")
