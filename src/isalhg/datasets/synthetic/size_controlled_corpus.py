"""Size-controlled planted-family corpus — one (n, m, k, degree-sequence) cell.

The T-M4b replacement for the size-heterogeneous Stratum A corpus: every item
in a cell shares the *same* vertex count, hyperedge count, arity sequence
(k-uniform), and exact per-vertex degree sequence, so the two naive baselines
(``size_l1`` = |Δn| + |Δm| and ``degree_seq_l1``) are identically zero on
every pair by construction.  Whatever a representation scores on this corpus
is higher-order structural signal, not size signal.

Construction (deterministic under ``(params, seed_value)``):

1. **Base.** One random connected ``k``-uniform hypergraph at ``(n, m)``.
2. **Family seeds.** ``n_families`` independent long chains of
   connectivity-preserving incidence swaps (``sep_swaps`` accepted swaps each)
   started from the base.  Every chain preserves the base's degree sequence
   exactly; the chains are pairwise far apart in edit space and are verified
   pairwise non-isomorphic.
3. **Members.** Each family seed is perturbed with ``t_swaps`` incidence swaps
   per member (``PlantedFamilyDataset`` with ``edit_kind="swap"``): connected,
   pairwise non-isomorphic within the family, family index as class label.

Restriction: stdlib + ``isalhg.core`` + ``isalhg.datasets``; the iso backend
import is deferred (inside the build) as in ``planted_families``.
"""

from __future__ import annotations

import logging
import random
from collections.abc import Iterator
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph, random_swap_edit
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import (
    DatasetItem,
    DatasetMetadata,
    LabelVocabulary,
    RealizedParams,
)
from isalhg.datasets.synthetic._random_hg import random_connected_hypergraph
from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset
from isalhg.types import DatasetName, Seed

logger = logging.getLogger(__name__)

# Distinct PRNG stream offsets: the base draw and each family's separation
# chain must not share a stream with PlantedFamilyDataset's member streams
# (which use seed_value + f * 999_983).
_BASE_OFFSET = 104_729
_CHAIN_STRIDE = 1_000_003


def _degree_sequence(H: SparseHypergraph) -> tuple[int, ...]:
    return tuple(sorted(H.degree(v) for v in range(H.n_nodes)))


def _connected_swap_chain(
    H: SparseHypergraph,
    n_swaps: int,
    rng: random.Random,
    max_attempts_per_swap: int = 200,
) -> SparseHypergraph:
    """Apply ``n_swaps`` connectivity-preserving incidence swaps to ``H``.

    Parameters
    ----------
    H : SparseHypergraph
        Starting hypergraph (unchanged).
    n_swaps : int
        Number of accepted swaps.
    rng : random.Random
        Seeded generator.
    max_attempts_per_swap : int, optional
        Rejection budget per accepted swap.

    Returns
    -------
    SparseHypergraph
        The endpoint of the chain; same degree sequence, arity sequence,
        ``n_nodes`` and ``n_edges`` as ``H``.

    Raises
    ------
    RuntimeError
        If a swap cannot be found within the attempt budget.
    """
    current = H
    for step in range(n_swaps):
        accepted: SparseHypergraph | None = None
        for _ in range(max_attempts_per_swap):
            candidate = random_swap_edit(current, rng)
            if candidate is not None and candidate.is_connected():
                accepted = candidate
                break
        if accepted is None:
            raise RuntimeError(
                f"no connectivity-preserving swap found at chain step {step}"
                f" within {max_attempts_per_swap} attempts"
            )
        current = accepted
    return current


class SizeControlledCellDataset(HypergraphDataset):
    """Planted swap-families at one fixed ``(n, m, k, degree-sequence)`` cell.

    Parameters
    ----------
    n_nodes : int
        Vertex count shared by every item.
    n_edges : int
        Hyperedge count shared by every item.
    k : int, optional
        Uniform hyperedge arity.  Default ``3``.
    n_families : int, optional
        Number of planted families (class labels).  Default ``12``.
    members_per_family : int, optional
        Members per family, the family seed included.  Default ``6``.
    t_swaps : int, optional
        Incidence swaps applied per non-seed member.  Default ``2``.
    sep_swaps : int | None, optional
        Length of each family seed's separation chain.  Default
        ``10 * n_edges``.
    max_retries : int, optional
        Rejection budget per member (forwarded to the family builder).
        Default ``200``.
    seed_value : int, optional
        Master seed; the whole corpus is a pure function of
        ``(params, seed_value)``.  Default ``0``.
    dedup_backend : str, optional
        Iso backend for non-iso checks.  Default ``"pynauty_levi"`` (fast
        oracle; matches the sweep harness).
    allow_partial : bool, optional
        Accept short families on retry exhaustion instead of raising.
        Default ``True``.

    Raises
    ------
    ValueError
        If two family seeds are isomorphic (astronomically unlikely at the
        default ``sep_swaps``), so a silent class collapse cannot occur.
    """

    def __init__(
        self,
        *,
        n_nodes: int,
        n_edges: int,
        k: int = 3,
        n_families: int = 12,
        members_per_family: int = 6,
        t_swaps: int = 2,
        sep_swaps: int | None = None,
        max_retries: int = 200,
        seed_value: int = 0,
        dedup_backend: str = "pynauty_levi",
        allow_partial: bool = True,
    ) -> None:
        self._params: dict[str, Any] = {
            "n_nodes": n_nodes,
            "n_edges": n_edges,
            "k": k,
            "n_families": n_families,
            "members_per_family": members_per_family,
            "t_swaps": t_swaps,
            "sep_swaps": sep_swaps,
            "max_retries": max_retries,
            "dedup_backend": dedup_backend,
            "allow_partial": allow_partial,
        }
        self._seed_value = int(seed_value)
        resolved_sep = sep_swaps if sep_swaps is not None else 10 * n_edges

        # random_connected_hypergraph treats n_edges as insertion *attempts*
        # (duplicate draws are dropped), so the realized (n, m) can fall short
        # of the requested cell; the cell contract is exact, so reject and
        # redraw until it is met.
        base_rng = random.Random(self._seed_value + _BASE_OFFSET)
        base: SparseHypergraph | None = None
        for _ in range(max_retries):
            candidate_base, _attempts = random_connected_hypergraph(
                n_nodes=n_nodes,
                n_edges=n_edges,
                arity_range=(k, k),
                rng=base_rng,
            )
            if (candidate_base.n_nodes, candidate_base.n_edges) == (n_nodes, n_edges):
                base = candidate_base
                break
        if base is None:
            raise RuntimeError(
                f"could not realize an exact ({n_nodes}, {n_edges}) connected"
                f" {k}-uniform base in {max_retries} draws"
            )
        ref_degseq = _degree_sequence(base)

        family_seeds: list[SparseHypergraph] = []
        for f in range(n_families):
            chain_rng = random.Random(self._seed_value + _BASE_OFFSET + (f + 1) * _CHAIN_STRIDE)
            family_seeds.append(_connected_swap_chain(base, resolved_sep, chain_rng))

        from isalhg.iso_backends.registry import get_backend  # deferred

        backend = get_backend(dedup_backend)
        fps = [backend.fingerprint(H) for H in family_seeds]
        if len(set(fps)) != len(fps):
            raise ValueError(
                f"two family seeds are isomorphic (sep_swaps={resolved_sep},"
                f" seed_value={self._seed_value}); increase sep_swaps"
            )

        inner = PlantedFamilyDataset(
            seeds=family_seeds,
            members_per_family=members_per_family,
            n_edits=t_swaps,
            max_retries=max_retries,
            seed_value=self._seed_value,
            dedup_backend=dedup_backend,
            allow_partial=allow_partial,
            edit_kind="swap",
        )

        cell_tag = f"n{n_nodes}m{n_edges}k{k}"
        items: list[DatasetItem] = []
        for item in inner:
            H = item.hypergraph
            if _degree_sequence(H) != ref_degseq or (H.n_nodes, H.n_edges) != (
                n_nodes,
                n_edges,
            ):
                raise RuntimeError(
                    f"size/degree control violated by item {item.item_id}"
                    " — the swap generator produced an out-of-cell member"
                )
            extra = dict(item.extra)
            extra["cell"] = (n_nodes, n_edges)
            extra["k"] = k
            items.append(
                DatasetItem(
                    item_id=f"{cell_tag}_{item.item_id}",
                    hypergraph=H,
                    iso_class=item.iso_class,
                    extra=extra,
                )
            )
        self._items = items

        rp = RealizedParams.compute([it.hypergraph for it in items], seeds=(self._seed_value,))
        self._metadata = DatasetMetadata(
            name="size_controlled_corpus",
            n_items=len(items),
            arity_range=(k, k),
            n_nodes_range=(n_nodes, n_nodes),
            has_iso_labels=False,
            source=(
                f"SizeControlledCellDataset(n_nodes={n_nodes}, n_edges={n_edges},"
                f" k={k}, n_families={n_families},"
                f" members_per_family={members_per_family}, t_swaps={t_swaps},"
                f" sep_swaps={resolved_sep}, seed_value={self._seed_value})"
            ),
            label_vocabulary=LabelVocabulary.trivial(),
            realized_params=rp,
        )

    # ------------------------------------------------------------------
    # HypergraphDataset ABC
    # ------------------------------------------------------------------

    @property
    def name(self) -> DatasetName:
        return "size_controlled_corpus"

    @property
    def metadata(self) -> DatasetMetadata:
        return self._metadata

    def __iter__(self) -> Iterator[DatasetItem]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def seed(self, seed: Seed) -> SizeControlledCellDataset:
        """Return a full rebuild under ``seed`` (base, chains, and members)."""
        return SizeControlledCellDataset(**self._params, seed_value=int(seed))


def _factory(params: dict[str, Any]) -> SizeControlledCellDataset:
    return SizeControlledCellDataset(**params)


register_dataset("size_controlled_corpus", _factory)
