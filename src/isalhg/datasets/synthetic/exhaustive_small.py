"""Tier 1 dataset: connected hypergraphs in a small parameter window.

Enumerates raw edge subsets via :mod:`itertools` over the
``range(n)``-arity candidate universe, filters by
:meth:`SparseHypergraph.is_connected`, and deduplicates iso-classes via
:meth:`IsalHGBackend.fingerprint`. This is the implementation of the
"itertools + fingerprint-dedup" mechanism replacing the XGI-enumeration
text in ``docs/preprint/PROPOSAL.md`` Tier 1 (resolution I2 in the Phase 3 plan).

Iteration yields, for each iso-class, one canonical representative plus
``permutations_per_class - 1`` random vertex permutations sharing the same
``iso_class`` label. This populates both the FP and FN cells of the
pairwise-iso confusion matrix.

The class also yields the named published designs (Fano plane STS(7),
STS(9), a non-iso cyclic-13 pair, GQ(2,2) doily) when
``include_designs=True``; each is deduplicated against the enumerated
classes so the resulting partition is sound.

Restriction: only Python stdlib + :mod:`isalhg.core` +
:mod:`isalhg.iso_backends` (used as the dedup oracle).
"""

from __future__ import annotations

import itertools
import random
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.datasets.synthetic import designs
from isalhg.iso_backends.base import IsoBackend
from isalhg.iso_backends.registry import get_backend
from isalhg.types import DatasetName, HyperedgeSet, IsoClassId, Seed


def _resolve_dedup_backend(name: str) -> IsoBackend:
    """Look up a backend by name through the registry.

    Used as the iso-class dedup oracle inside enumeration. Any registered
    backend whose ``fingerprint`` is deterministic and iso-invariant
    suffices.
    """
    return get_backend(name)


# ---------------------------------------------------------------------------
# Named published designs (resolution D1 / open question Q1 — Feng / Zhang
# Fig. 3 pairs are deferred to Phase 3.5).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _NamedDesign:
    name: str
    n_nodes: int
    edges: tuple[HyperedgeSet, ...]
    citation: str


def _named(name: str, H: SparseHypergraph, citation: str) -> _NamedDesign:
    return _NamedDesign(
        name=name,
        n_nodes=H.n_nodes,
        edges=tuple(members for _, members, _ in H.iter_edges()),
        citation=citation,
    )


def _fano_plane() -> _NamedDesign:
    return _named("fano_plane_sts7", designs.fano_plane(), "Fano (1892); STS(7) = PG(2, 2)")


def _sts_9() -> _NamedDesign:
    return _named("sts_9_ag23", designs.sts_9(), "AG(2, 3) Steiner triple system")


def _sts_13_pair_a() -> _NamedDesign:
    """One cyclic orbit of triples on Z/13Z from the starter {0, 1, 4}.

    Not an STS(13) despite the item id: a single starter covers 39 of the 78
    point-pairs. Kept as-is because callers use it only as a 3-uniform,
    vertex-transitive hard instance and as one half of a non-isomorphic pair.
    """
    return _named(
        "sts_13_cyclic_014",
        designs.cyclic_sts_13((0, 1, 4)),
        "Bose 1939; cyclic triple orbit from {0,1,4} mod 13",
    )


def _sts_13_pair_b() -> _NamedDesign:
    """The companion cyclic orbit from the starter {0, 1, 6}.

    Non-isomorphic to :func:`_sts_13_pair_a`; the Phase 3 closing check
    verifies this empirically via the IsalHG and pynauty backends. See that
    function on why neither is a Steiner triple system.
    """
    return _named(
        "sts_13_cyclic_016",
        designs.cyclic_sts_13((0, 1, 6)),
        "cyclic triple orbit from {0,1,6} mod 13",
    )


def _gq_2_2_doily() -> _NamedDesign:
    """Generalised quadrangle GQ(2, 2), the "doily": 15 points, 15 lines."""
    return _named(
        "gq_2_2_doily",
        designs.gq_2_2_doily(),
        "Sylvester 1861 duad-syntheme model; Payne & Thas, FGQ §1.2 (W(2))",
    )


def _small_named_designs() -> tuple[_NamedDesign, ...]:
    """Cheap-to-fingerprint named designs (Fano, STS(9))."""
    return (_fano_plane(), _sts_9())


def _large_named_designs() -> tuple[_NamedDesign, ...]:
    """High-automorphism designs (the cyclic-13 pair, GQ(2,2)).

    The bounded backtracking in
    :func:`isalhg.core.hypergraph_to_string._encode_from` is exponential
    in the size of the class-symmetry orbit on these structures (open
    research question #1 in ``docs/engineering/DEVELOPMENT.md``), so they are
    gated behind ``include_large_designs=True`` and Tier 1 unit tests do not
    pay the cost; the Phase-4 closing check explicitly opts in.
    """
    return (_sts_13_pair_a(), _sts_13_pair_b(), _gq_2_2_doily())


# ---------------------------------------------------------------------------
# Dataset class
# ---------------------------------------------------------------------------


class ExhaustiveSmallHypergraphs(HypergraphDataset):
    """Connected hypergraphs in a small ``(n, arity, m)`` window.

    Parameters
    ----------
    n_range : tuple[int, int]
        Inclusive ``(min_n, max_n)`` over the vertex count.
    arity_range : tuple[int, int]
        Inclusive ``(min_arity, max_arity)`` over hyperedge sizes.
    max_edges : int
        Cap on the edge-count ``m`` per enumerated hypergraph. Required
        because the universe ``2^(sum_arity C(n, a))`` grows
        super-exponentially in ``n``.
    include_designs : bool
        If True, the iterator also yields the cheap published designs
        (Fano, STS(9)) deduplicated against the enumerated iso-classes.
    include_large_designs : bool
        If True, additionally yields the high-automorphism designs
        (cyclic-13 pair, GQ(2,2) doily). Off by default because IsalHG
        fingerprinting on these structures is orders of magnitude slower
        than on the small ones (open question #1).
    dedup_backend_name : str
        Backend name used as the iso-class dedup oracle inside this
        dataset. ``"isalhg"`` (default) is pure stdlib but slow on
        high-automorphism inputs; ``"pynauty_levi"`` is orders of
        magnitude faster and recommended whenever pynauty is installed.
        The choice does not affect which backend is later tested in the
        protocol layer.
    permutations_per_class : int
        For every iso-class, emit one canonical representative plus
        ``permutations_per_class - 1`` random permutations (sharing the
        same ``iso_class`` ID). ``>= 2`` is needed to exercise the FN
        cell of the pairwise-iso confusion matrix.
    seed_value : Seed
        Seed for the per-class permutation PRNG. Identical seeds produce
        identical iteration sequences.
    """

    def __init__(
        self,
        n_range: tuple[int, int] = (3, 6),
        arity_range: tuple[int, int] = (2, 4),
        *,
        max_edges: int = 6,
        include_designs: bool = True,
        include_large_designs: bool = False,
        dedup_backend_name: str = "isalhg",
        permutations_per_class: int = 2,
        seed_value: Seed = 0,
    ) -> None:
        if n_range[0] < 1 or n_range[1] < n_range[0]:
            raise ValueError(f"invalid n_range {n_range}")
        if arity_range[0] < 1 or arity_range[1] < arity_range[0]:
            raise ValueError(f"invalid arity_range {arity_range}")
        if max_edges < 1:
            raise ValueError("max_edges must be >= 1")
        if permutations_per_class < 1:
            raise ValueError("permutations_per_class must be >= 1")
        # Validate the dedup backend at construction so the user gets a
        # clean BackendUnavailableError up-front rather than hours into
        # the enumeration loop.
        _resolve_dedup_backend(dedup_backend_name)
        self._n_range = n_range
        self._arity_range = arity_range
        self._max_edges = max_edges
        self._include_designs = include_designs
        self._include_large_designs = include_large_designs
        self._dedup_backend_name = dedup_backend_name
        self._permutations_per_class = permutations_per_class
        self._seed_value = seed_value
        self._reps_cache: list[tuple[bytes, SparseHypergraph, dict[str, Any]]] | None = None

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def name(self) -> DatasetName:
        return "exhaustive_small"

    @property
    def metadata(self) -> DatasetMetadata:
        reps = self._ensure_reps()
        n_min = min(H.n_nodes for _, H, _ in reps) if reps else self._n_range[0]
        n_max = max(H.n_nodes for _, H, _ in reps) if reps else self._n_range[1]
        a_min_obs = self._arity_range[0]
        a_max_obs = self._arity_range[1]
        if reps:
            arities: set[int] = set()
            for _, H, _ in reps:
                for _e, members, _l in H.iter_edges():
                    arities.add(len(members))
            if arities:
                a_min_obs = min(arities)
                a_max_obs = max(arities)
        return DatasetMetadata(
            name=self.name,
            n_items=len(self),
            arity_range=(a_min_obs, a_max_obs),
            n_nodes_range=(n_min, n_max),
            has_iso_labels=True,
            source=(
                "itertools edge-subset enumeration + "
                f"{self._dedup_backend_name!r} fingerprint dedup"
            ),
            citation="PROPOSAL.md Tier 1 (resolution I2; D1 defers Feng/Zhang Fig. 3 pairs)",
            label_vocabulary=LabelVocabulary.trivial(),
        )

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[DatasetItem]:
        reps = self._ensure_reps()
        rng = random.Random(self._seed_value)
        for class_id, (_fp, H_canonical, extra) in enumerate(reps):
            yield DatasetItem(
                item_id=f"class{class_id:04d}_rep0",
                hypergraph=H_canonical,
                iso_class=class_id,
                extra={**extra, "permutation_index": 0},
            )
            for k in range(1, self._permutations_per_class):
                sigma = list(range(H_canonical.n_nodes))
                rng.shuffle(sigma)
                H_perm = permute(H_canonical, sigma)
                yield DatasetItem(
                    item_id=f"class{class_id:04d}_rep{k}",
                    hypergraph=H_perm,
                    iso_class=class_id,
                    extra={**extra, "permutation_index": k, "sigma": tuple(sigma)},
                )

    def __len__(self) -> int:
        return len(self._ensure_reps()) * self._permutations_per_class

    def seed(self, seed: Seed) -> HypergraphDataset:
        return ExhaustiveSmallHypergraphs(
            n_range=self._n_range,
            arity_range=self._arity_range,
            max_edges=self._max_edges,
            include_designs=self._include_designs,
            include_large_designs=self._include_large_designs,
            dedup_backend_name=self._dedup_backend_name,
            permutations_per_class=self._permutations_per_class,
            seed_value=seed,
        )

    # ------------------------------------------------------------------
    # Enumeration core
    # ------------------------------------------------------------------

    def _ensure_reps(self) -> list[tuple[bytes, SparseHypergraph, dict[str, Any]]]:
        if self._reps_cache is None:
            self._reps_cache = list(self._collect_iso_reps())
        return self._reps_cache

    def _collect_iso_reps(self) -> Iterator[tuple[bytes, SparseHypergraph, dict[str, Any]]]:
        """Enumerate connected hypergraphs and yield ``(fp, canonical_H, extra)``.

        One yield per fresh iso-class fingerprint. The order is:
        (1) ``itertools`` enumeration in ``n`` ascending, then edge-count
        ascending, then deterministic combination order; (2) the named
        designs (small first, large second when opted in). Named designs
        whose fingerprint matches an already-enumerated class are
        dropped so iso-class IDs stay stable across the
        ``include_designs`` toggle.
        """
        backend = _resolve_dedup_backend(self._dedup_backend_name)
        seen: dict[bytes, IsoClassId] = {}
        n_min, n_max = self._n_range
        a_min, a_max = self._arity_range
        next_id: IsoClassId = 0

        for n in range(n_min, n_max + 1):
            candidates: list[HyperedgeSet] = []
            for arity in range(a_min, a_max + 1):
                if arity > n:
                    continue
                candidates.extend(frozenset(c) for c in itertools.combinations(range(n), arity))
            if not candidates:
                continue
            m_cap = min(self._max_edges, len(candidates))
            for m in range(1, m_cap + 1):
                for subset in itertools.combinations(candidates, m):
                    # Necessary connectivity condition: every vertex is touched.
                    union: set[int] = set()
                    for e in subset:
                        union.update(e)
                    if len(union) != n:
                        continue
                    H = SparseHypergraph(n_nodes=n, hyperedges=list(subset))
                    if not H.is_connected():
                        continue
                    fp = backend.fingerprint(H)
                    if fp in seen:
                        continue
                    seen[fp] = next_id
                    extra: dict[str, Any] = {
                        "source": "exhaustive_enum",
                        "n_nodes": n,
                        "n_edges": m,
                    }
                    yield fp, H, extra
                    next_id += 1

        designs: tuple[_NamedDesign, ...] = ()
        if self._include_designs:
            designs = designs + _small_named_designs()
        if self._include_large_designs:
            designs = designs + _large_named_designs()
        if designs:
            for design in designs:
                H = SparseHypergraph(n_nodes=design.n_nodes, hyperedges=list(design.edges))
                fp = backend.fingerprint(H)
                if fp in seen:
                    # Same iso-class as an enumerated representative: drop the
                    # design here. (Tier 1 acceptance verifies non-isomorphism
                    # via cross-class pairs; an enumerated representative
                    # already exercises this fingerprint.)
                    continue
                seen[fp] = next_id
                extra = {
                    "source": "named_design",
                    "design_name": design.name,
                    "citation": design.citation,
                    "n_nodes": design.n_nodes,
                    "n_edges": len(design.edges),
                }
                yield fp, H, extra
                next_id += 1


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def _coerce_pair(value: Any, default: tuple[int, int]) -> tuple[int, int]:
    if value is None:
        return default
    seq = list(value)
    if len(seq) != 2:
        raise ValueError(f"expected 2-element sequence, got {seq!r}")
    return (int(seq[0]), int(seq[1]))


def _factory(params: dict[str, Any]) -> HypergraphDataset:
    return ExhaustiveSmallHypergraphs(
        n_range=_coerce_pair(params.get("n_range"), (3, 6)),
        arity_range=_coerce_pair(params.get("arity_range"), (2, 4)),
        max_edges=int(params.get("max_edges", 6)),
        include_designs=bool(params.get("include_designs", True)),
        include_large_designs=bool(params.get("include_large_designs", False)),
        dedup_backend_name=str(params.get("dedup_backend_name", "isalhg")),
        permutations_per_class=int(params.get("permutations_per_class", 2)),
        seed_value=int(params.get("seed_value", 0)),
    )


register_dataset("exhaustive_small", _factory)
