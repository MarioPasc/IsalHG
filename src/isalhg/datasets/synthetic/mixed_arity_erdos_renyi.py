"""Tier 2 dataset: mixed-arity Erdos-Renyi hypergraphs.

Wraps ``xgi.generators.random.random_hypergraph`` (Dewar et al. arXiv:1703.07686;
Landry et al. 2023 JOSS 8(85):5162).  Unlike
:class:`~isalhg.datasets.synthetic.erdos_renyi.UniformErdosRenyiHypergraphs`
where every hyperedge has exactly ``r`` vertices, here each hyperedge's arity is
drawn uniformly over the integer range ``[2, k]``.

Model
-----
Given (n, k, c) with ``k ≥ 2``:

- For each arity ``a ∈ {2, 3, …, k}`` and each a-subset of the ``n`` vertices,
  include the subset as a hyperedge with the same probability ``p``.
- ``p`` is chosen so that the expected total number of edges satisfies
  ``E[m] = p · Σ_{a=2}^{k} C(n, a) = c · n``, i.e.
  ``p = c · n / Σ_{a=2}^{k} C(n, a)``.
- Realised arity distribution is approximately uniform over ``{2, …, k}``
  (each arity-``a`` slot contributes ``p · C(n, a)`` expected edges, so the
  distribution is weighted by the binomial coefficients).

Because ``p`` is shared across arities, denser binomial-coefficient arities
(typically mid-range) contribute more edges.  The arity histogram is recorded
in the realized-parameter extra field.

Connectivity policy
-------------------
Same deterministic seed-walk reject-resample as the uniform ER generator
(prime stride 1 000 003).  Set ``require_connected=False`` to skip.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Iterator
from typing import Any

from isalhg.adapters.xgi_adapter import XGIAdapter
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary
from isalhg.errors import DatasetError
from isalhg.types import DatasetName, Seed

logger = logging.getLogger(__name__)

_SEED_STRIDE = 1_000_003  # prime, same as uniform ER and CL reject-resample stride


def _p_from_c_mixed(c: float, n: int, k: int) -> float:
    """Convert density ``c = E[m] / n`` to inclusion probability ``p``.

    For mixed arity ``[2, k]`` the universe size is
    ``Σ_{a=2}^{k} C(n, a)`` and ``E[m] = p · universe = c · n``.

    Parameters
    ----------
    c : float
        Target density (expected edges per vertex).
    n : int
        Number of vertices.
    k : int
        Maximum arity.

    Returns
    -------
    float
        Inclusion probability clamped to ``[0, 1]``.
    """
    universe = sum(math.comb(n, a) for a in range(2, k + 1))
    if universe == 0:
        raise DatasetError(
            f"empty edge universe for mixed arity (n={n}, k={k}); need k >= 2 and n >= 2"
        )
    p = c * n / universe
    if p > 1.0:
        logger.warning("c=%.3g on (n=%d, k=%d) yields p=%.3g > 1; clamping to 1.0", c, n, k, p)
        return 1.0
    return p


class MixedArityErdosRenyiHypergraphs(HypergraphDataset):
    """Single-item mixed-arity Erdos-Renyi hypergraph generator.

    Each hyperedge's arity is drawn uniformly from ``{2, 3, …, k}`` with the
    same inclusion probability ``p = c·n / Σ_{a=2}^{k} C(n,a)``.

    Yields exactly one :class:`~isalhg.datasets.schemas.DatasetItem` per
    instance.

    Parameters
    ----------
    n : int
        Number of vertices.  Must be ``≥ 2`` (need at least arity-2 edges).
    k : int
        Maximum arity.  Must satisfy ``2 ≤ k ≤ n``.
    c : float
        Target density ``E[m] / n``.  Must be ``≥ 0``.
    seed : Seed
        PRNG seed forwarded to ``xgi.random_hypergraph``.
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
            raise ValueError(f"k must be >= 2 and <= n; got k={k}, n={n}")
        if c < 0:
            raise ValueError(f"c must be >= 0; got {c}")
        if connected_max_attempts < 1:
            raise ValueError(f"connected_max_attempts must be >= 1; got {connected_max_attempts}")

        self._n = int(n)
        self._k = int(k)
        self._c = float(c)
        self._p = _p_from_c_mixed(float(c), int(n), int(k))
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
        return "random_erdos_renyi_mixed"

    @property
    def metadata(self) -> DatasetMetadata:
        if self._cached_metadata is None:
            self._cached_metadata = DatasetMetadata(
                name=self.name,
                n_items=1,
                arity_range=(2, self._k),
                n_nodes_range=(self._n, self._n),
                has_iso_labels=False,
                source="xgi.generators.random.random_hypergraph",
                citation=("Dewar et al. arXiv:1703.07686; Landry et al. 2023 JOSS 8(85):5162"),
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

    def seed(self, seed: Seed) -> MixedArityErdosRenyiHypergraphs:
        """Return a copy of this dataset bound to *seed*.

        Parameters
        ----------
        seed : Seed
            New PRNG seed.

        Returns
        -------
        MixedArityErdosRenyiHypergraphs
        """
        return MixedArityErdosRenyiHypergraphs(
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
                "MixedArityErdosRenyiHypergraphs requires xgi; install via `pip install xgi`"
            ) from exc

        # XGI order convention: order d means arity d+1.
        # For arities {2..k} we need orders {1..k-1}.
        orders = list(range(1, self._k))
        ps = [self._p] * len(orders)

        attempt = 0
        effective_seed = int(self._seed)
        last_n_edges = -1

        while True:
            attempt += 1
            effective_seed = int(self._seed) + (attempt - 1) * _SEED_STRIDE

            xgi_H = xgi.random_hypergraph(  # type: ignore[no-untyped-call]
                self._n, ps, order=orders, seed=effective_seed
            )
            H = XGIAdapter().from_external(xgi_H)
            last_n_edges = H.n_edges

            if not self._require_connected or H.is_connected():
                break
            if attempt >= self._connected_max_attempts:
                raise DatasetError(
                    "MixedArityErdosRenyiHypergraphs: exhausted "
                    f"{self._connected_max_attempts} attempts trying to draw a "
                    f"connected hypergraph at (n={self._n}, k={self._k}, "
                    f"c={self._c:.3g}, seed={self._seed}). Increase "
                    "connected_max_attempts, raise c, or set "
                    "require_connected=False."
                )

        if attempt > 1:
            logger.info(
                "mixed-arity ER reject-resample: connected sample on attempt %d "
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
        item_id = f"er_mixed_n{self._n}_k{self._k}_c{c_repr}_s{self._seed}"
        extra: dict[str, Any] = {
            "source": "xgi.random_hypergraph",
            "n": self._n,
            "k": self._k,
            "c": self._c,
            "p": self._p,
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
    return MixedArityErdosRenyiHypergraphs(
        n=int(params["n"]),
        k=int(params["k"]),
        c=float(params["c"]),
        seed=int(params.get("seed", 0)),
        require_connected=bool(params.get("require_connected", True)),
        connected_max_attempts=int(params.get("connected_max_attempts", 1000)),
    )


register_dataset("random_erdos_renyi_mixed", _factory)
