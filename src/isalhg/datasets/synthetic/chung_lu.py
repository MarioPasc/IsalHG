"""Tier 2 dataset: Chung-Lu hypergraphs (parametric single-item generator).

Wraps ``xgi.generators.random.chung_lu_hypergraph`` (Chodrow, 2020,
arXiv:1902.09302). Generates one connected hypergraph per instance from a
bipartite Chung-Lu model with a harmonic node-degree distribution and
uniform target edge arity ``k``.

Interface mirrors :class:`~isalhg.datasets.synthetic.erdos_renyi.UniformErdosRenyiHypergraphs`
so that the Stratum B sweep can drive both generators from the same (n, k, c,
seed) parameter triple.

Model
-----
Given (n, k, c):
- Expected number of edges: ``m = max(1, round(c * n))``.
- Edge-size sequence (k2): every edge has expected arity ``k``, so
  ``k2 = {j: k  for j in range(m)}``.
- Node-degree sequence (k1): harmonic weights
  ``w_i = 1 / (i + 1)`` for ``i = 0…n-1``, scaled to sum ``m * k``, then
  rounded to non-negative integers with the exact sum enforced.
- ``xgi.chung_lu_hypergraph(k1, k2, seed=seed)`` assigns each node ``i`` to
  each edge ``j`` independently with probability ``k1[i] * k2[j] / S`` where
  ``S = sum(k1) = sum(k2) = m * k``.

Because the model is probabilistic, realized edge arities deviate from ``k``;
the arity histogram is part of the realized-parameter record.

Connectivity policy
-------------------
By default the generator rejects disconnected samples and redraws with a
deterministic seed walk ``seed, seed + 1_000_003, seed + 2·1_000_003, …``
(same stride as :class:`~isalhg.datasets.synthetic.erdos_renyi.UniformErdosRenyiHypergraphs`).
Set ``require_connected=False`` to skip the connectivity check.
"""

from __future__ import annotations

import logging
import warnings
from collections.abc import Iterator
from typing import Any

from isalhg.adapters.xgi_adapter import XGIAdapter
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.errors import DatasetError
from isalhg.types import DatasetName, Seed

logger = logging.getLogger(__name__)

_SEED_STRIDE = 1_000_003  # prime, same as ER reject-resample stride


def _harmonic_degree_sequence(n: int, total_degree: int) -> list[int]:
    """Harmonic node-degree sequence summing exactly to *total_degree*.

    Node ``i`` gets weight ``1 / (i + 1)``, scaled to ``total_degree``.  The
    result is rounded to non-negative integers and adjusted so that
    ``sum(result) == total_degree`` exactly.

    Parameters
    ----------
    n : int
        Number of nodes.
    total_degree : int
        Required sum of the degree sequence.

    Returns
    -------
    list[int]
        Integer degree sequence of length ``n`` summing to ``total_degree``.
    """
    if n == 0 or total_degree == 0:
        return [0] * n

    weights = [1.0 / (i + 1) for i in range(n)]
    wsum = sum(weights)
    raw = [w * total_degree / wsum for w in weights]
    degrees = [max(0, int(d)) for d in raw]

    current = sum(degrees)
    diff = total_degree - current

    if diff > 0:
        # Increment nodes with the largest fractional remainder first.
        fracs = sorted(range(n), key=lambda i: raw[i] - int(raw[i]), reverse=True)
        for i in fracs[:diff]:
            degrees[i] += 1
    elif diff < 0:
        # Decrement nodes with the largest degree first.
        for _ in range(-diff):
            idx = max(range(n), key=lambda i: degrees[i])
            if degrees[idx] > 0:
                degrees[idx] -= 1

    return degrees


class ChungLuHypergraphs(HypergraphDataset):
    """Single-item parametric Chung-Lu hypergraph generator.

    Yields exactly one :class:`~isalhg.datasets.schemas.DatasetItem` per
    instance; the Stratum B sweep addresses each ``(n, k, c, seed)`` cell as a
    separate :class:`~experiments.schemas.CellSpec`.

    Parameters
    ----------
    n : int
        Number of vertices.  Must be ``≥ 1``.
    k : int
        Target uniform edge arity (expected arity per hyperedge).
        Must satisfy ``2 ≤ k ≤ n``.
    c : float
        Target density ``m / n`` (expected edges per vertex).  Must be ``≥ 0``.
    seed : Seed
        PRNG seed forwarded to ``xgi.chung_lu_hypergraph``.
    require_connected : bool
        If ``True`` (default), reject disconnected samples and redraw using
        the deterministic seed walk.
    connected_max_attempts : int
        Maximum rejection-resample attempts before raising
        :class:`~isalhg.errors.DatasetError`.
    """

    def __init__(
        self,
        *,
        n: int,
        k: int,
        c: float,
        seed: Seed = 0,
        require_connected: bool = True,
        connected_max_attempts: int = 1000,
    ) -> None:
        if n < 1:
            raise ValueError(f"n must be >= 1, got {n}")
        if k < 2 or k > n:
            raise ValueError(f"k must satisfy 2 <= k <= n; got k={k}, n={n}")
        if c < 0:
            raise ValueError(f"c must be >= 0; got {c}")
        if connected_max_attempts < 1:
            raise ValueError(f"connected_max_attempts must be >= 1; got {connected_max_attempts}")

        self._n = int(n)
        self._k = int(k)
        self._c = float(c)
        self._seed: Seed = int(seed)
        self._require_connected = bool(require_connected)
        self._connected_max_attempts = int(connected_max_attempts)
        self._cached_item: DatasetItem | None = None
        self._cached_metadata: DatasetMetadata | None = None

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def name(self) -> DatasetName:
        return "chung_lu"

    @property
    def metadata(self) -> DatasetMetadata:
        if self._cached_metadata is None:
            item = self._materialise()
            h = item.hypergraph
            arities = [len(members) for _, members, _ in h.iter_edges()]
            lo = min(arities) if arities else self._k
            hi = max(arities) if arities else self._k
            self._cached_metadata = DatasetMetadata(
                name=self.name,
                n_items=1,
                arity_range=(lo, hi),
                n_nodes_range=(self._n, self._n),
                has_iso_labels=False,
                source="xgi.generators.random.chung_lu_hypergraph",
                citation="Chodrow 2020 arXiv:1902.09302",
                label_vocabulary=LabelVocabulary.trivial(),
            )
        return self._cached_metadata

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[DatasetItem]:
        yield self._materialise()

    def __len__(self) -> int:
        return 1

    def seed(self, seed: Seed) -> ChungLuHypergraphs:
        """Return a copy of this dataset bound to *seed*.

        Parameters
        ----------
        seed : Seed
            New PRNG seed.

        Returns
        -------
        ChungLuHypergraphs
        """
        return ChungLuHypergraphs(
            n=self._n,
            k=self._k,
            c=self._c,
            seed=seed,
            require_connected=self._require_connected,
            connected_max_attempts=self._connected_max_attempts,
        )

    # ------------------------------------------------------------------
    # Materialisation
    # ------------------------------------------------------------------

    def _materialise(self) -> DatasetItem:
        if self._cached_item is not None:
            return self._cached_item

        try:
            import xgi
        except ImportError as exc:  # pragma: no cover
            raise DatasetError(
                "ChungLuHypergraphs requires xgi; install via `pip install xgi`"
            ) from exc

        m = max(1, round(self._c * self._n))
        total_degree = m * self._k
        node_degrees = _harmonic_degree_sequence(self._n, total_degree)

        k1 = {i: node_degrees[i] for i in range(self._n)}
        k2 = {j: self._k for j in range(m)}

        attempt = 0
        effective_seed = int(self._seed)
        last_n_edges = -1

        while True:
            attempt += 1
            effective_seed = int(self._seed) + (attempt - 1) * _SEED_STRIDE

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                xgi_H = xgi.chung_lu_hypergraph(k1, k2, seed=effective_seed)  # type: ignore[no-untyped-call]

            # Remove degenerate hyperedges: size < 2 (SparseHypergraph forbids
            # singletons) and size > k (the Chung-Lu bipartite model is
            # probabilistic and can produce edges beyond the arity cap).
            valid_edges = [
                list(xgi_H.edges.members(eid))
                for eid in xgi_H.edges
                if 2 <= len(xgi_H.edges.members(eid)) <= self._k
            ]
            xgi_H_clean = xgi.Hypergraph(valid_edges)  # type: ignore[no-untyped-call]
            # Restore all n node IDs: filtering edges may drop isolated nodes
            # from the XGI node set, causing the downstream SparseHypergraph
            # to have fewer than n_nodes vertices.
            xgi_H_clean.add_nodes_from(range(self._n))  # type: ignore[no-untyped-call]

            H = XGIAdapter().from_external(xgi_H_clean)
            last_n_edges = H.n_edges

            if not self._require_connected or H.is_connected():
                break
            if attempt >= self._connected_max_attempts:
                raise DatasetError(
                    "ChungLuHypergraphs: exhausted "
                    f"{self._connected_max_attempts} attempts trying to draw a "
                    f"connected hypergraph at (n={self._n}, k={self._k}, "
                    f"c={self._c:.3g}, seed={self._seed}). Increase "
                    "connected_max_attempts, raise c, or set "
                    "require_connected=False."
                )

        if attempt > 1:
            logger.info(
                "CL reject-resample: connected sample on attempt %d "
                "(n=%d, k=%d, c=%.3g, base seed=%d, effective seed=%d, "
                "n_edges=%d)",
                attempt,
                self._n,
                self._k,
                self._c,
                self._seed,
                effective_seed,
                last_n_edges,
            )

        c_repr = f"{self._c:g}"
        item_id = f"cl_n{self._n}_k{self._k}_c{c_repr}_s{self._seed}"
        extra: dict[str, Any] = {
            "source": "xgi.chung_lu_hypergraph",
            "n": self._n,
            "k": self._k,
            "c": self._c,
            "seed": self._seed,
            "effective_seed": effective_seed,
            "connected_attempts": attempt,
            "require_connected": self._require_connected,
            "n_edges": H.n_edges,
            "n_nodes": H.n_nodes,
        }
        self._cached_item = DatasetItem(
            item_id=item_id,
            hypergraph=H,
            iso_class=None,
            extra=extra,
        )
        return self._cached_item


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def _factory(params: dict[str, Any]) -> HypergraphDataset:
    return ChungLuHypergraphs(
        n=int(params["n"]),
        k=int(params["k"]),
        c=float(params["c"]),
        seed=int(params.get("seed", 0)),
        require_connected=bool(params.get("require_connected", True)),
        connected_max_attempts=int(params.get("connected_max_attempts", 1000)),
    )


register_dataset("chung_lu", _factory)
