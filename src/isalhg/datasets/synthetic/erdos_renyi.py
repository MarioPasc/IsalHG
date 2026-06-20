"""Preprint dataset: r-uniform Erdos-Renyi hypergraphs.

Thin wrapper around
``xgi.generators.uniform.uniform_erdos_renyi_hypergraph(n, m, p, p_type='prob',
multiedges=False, seed=seed)`` (Chodrow 2020 arXiv:1902.09302; Landry et al.
2023 JOSS 8(85):5162). One dataset instance yields **exactly one**
:class:`DatasetItem` — the orchestrator addresses every
``(backend, n, r, c, seed)`` cell as a separate :class:`CellSpec`, so the
dataset's only responsibility is to materialise the single hypergraph that
matches its constructor parameters.

Parameter conventions
---------------------
Two density parameterisations are supported:

- ``p`` — the underlying XGI per-edge inclusion probability.
- ``c`` — PI's "edges per vertex" target (PREPRINT.md §3, option b). The
  dataset translates ``c → p`` via ``p = c * n / C(n, r)``.

Exactly one of ``(p, c)`` must be set. ``c`` is the YAML-friendly axis used
throughout ``docs/PREPRINT.md``; ``p`` is the literal XGI argument.

No iso labels are produced (``has_iso_labels=False``); the
:class:`FingerprintTimingProtocol` constructs positive iso-pairs at
measurement time via :func:`isalhg.core.sparse_hypergraph.permute`.
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


def _p_from_c(c: float, n: int, r: int) -> float:
    """Convert the ``c`` edges-per-vertex target to the XGI probability ``p``.

    ``E[m] = p * C(n, r) = c * n`` ⇒ ``p = c * n / C(n, r)``. Saturates at
    1.0 when the requested density exceeds the universe.
    """
    universe = math.comb(n, r)
    if universe == 0:
        raise DatasetError(f"empty edge universe for (n={n}, r={r}); r must be <= n")
    p = c * n / universe
    if p > 1.0:
        logger.warning("c=%.3g on (n=%d, r=%d) yields p=%.3g > 1; clamping to 1.0", c, n, r, p)
        return 1.0
    return p


class UniformErdosRenyiHypergraphs(HypergraphDataset):
    """Single-item ``r``-uniform Erdos-Renyi hypergraph cohort.

    Parameters
    ----------
    n : int
        Vertex count.
    r : int
        Uniform arity. Every hyperedge contains exactly ``r`` distinct
        vertices.
    p : float | None
        XGI per-edge inclusion probability. Mutually exclusive with ``c``.
    c : float | None
        Edges-per-vertex target; translates internally to
        ``p = c * n / C(n, r)``. Mutually exclusive with ``p``.
    seed : Seed
        PRNG seed forwarded to ``xgi.uniform_erdos_renyi_hypergraph``.
    """

    def __init__(
        self,
        *,
        n: int,
        r: int,
        p: float | None = None,
        c: float | None = None,
        seed: Seed = 0,
    ) -> None:
        if n < 1:
            raise ValueError(f"n must be >= 1, got {n}")
        if r < 1 or r > n:
            raise ValueError(f"r must satisfy 1 <= r <= n; got r={r}, n={n}")
        if (p is None) == (c is None):
            raise ValueError(f"exactly one of (p, c) must be set; got p={p!r}, c={c!r}")
        if p is not None and not (0.0 <= p <= 1.0):
            raise ValueError(f"p must lie in [0, 1]; got {p}")
        if c is not None and c < 0:
            raise ValueError(f"c must be >= 0; got {c}")

        self._n = int(n)
        self._r = int(r)
        self._c: float | None = float(c) if c is not None else None
        self._p: float = (
            float(p) if p is not None else _p_from_c(float(c), self._n, self._r)  # type: ignore[arg-type]
        )
        self._seed: Seed = int(seed)
        self._cached_item: DatasetItem | None = None
        self._cached_metadata: DatasetMetadata | None = None

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def name(self) -> DatasetName:
        return "random_erdos_renyi"

    @property
    def metadata(self) -> DatasetMetadata:
        if self._cached_metadata is None:
            item = self._materialise()
            self._cached_metadata = DatasetMetadata(
                name=self.name,
                n_items=1,
                arity_range=(self._r, self._r),
                n_nodes_range=(self._n, self._n),
                has_iso_labels=False,
                source="xgi.generators.uniform.uniform_erdos_renyi_hypergraph",
                citation=("Chodrow 2020 arXiv:1902.09302; Landry et al. 2023 JOSS 8(85):5162"),
                label_vocabulary=LabelVocabulary.trivial(),
            )
            logger.debug(
                "metadata(n=%d, r=%d, p=%.3e, seed=%d) -> %d edges",
                self._n,
                self._r,
                self._p,
                self._seed,
                item.hypergraph.n_edges,
            )
        return self._cached_metadata

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[DatasetItem]:
        yield self._materialise()

    def __len__(self) -> int:
        return 1

    def seed(self, seed: Seed) -> UniformErdosRenyiHypergraphs:
        return UniformErdosRenyiHypergraphs(
            n=self._n,
            r=self._r,
            p=self._p,
            seed=seed,
        )

    # ------------------------------------------------------------------
    # Materialisation
    # ------------------------------------------------------------------

    def _materialise(self) -> DatasetItem:
        if self._cached_item is not None:
            return self._cached_item
        try:
            import xgi
        except ImportError as exc:  # pragma: no cover - xgi is a hard dep
            raise DatasetError(
                "UniformErdosRenyiHypergraphs requires xgi; install via `pip install xgi`"
            ) from exc

        # Note: positional API is (n, m, p, ...) where `m` is the arity (uniform
        # hyperedge size) and `p` is the probability when p_type='prob'.
        xgi_H = xgi.uniform_erdos_renyi_hypergraph(  # type: ignore[no-untyped-call]
            self._n,
            self._r,
            self._p,
            p_type="prob",
            multiedges=False,
            seed=self._seed,
        )
        H = XGIAdapter().from_external(xgi_H)
        c_repr = f"{self._c:g}" if self._c is not None else "na"
        item_id = f"er_n{self._n}_r{self._r}_c{c_repr}_s{self._seed}"
        extra: dict[str, Any] = {
            "source": "xgi.uniform_erdos_renyi_hypergraph",
            "n": self._n,
            "r": self._r,
            "p": self._p,
            "c": self._c,
            "seed": self._seed,
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
    return UniformErdosRenyiHypergraphs(
        n=int(params["n"]),
        r=int(params["r"]),
        p=(float(params["p"]) if params.get("p") is not None else None),
        c=(float(params["c"]) if params.get("c") is not None else None),
        seed=int(params.get("seed", 0)),
    )


register_dataset("random_erdos_renyi", _factory)
