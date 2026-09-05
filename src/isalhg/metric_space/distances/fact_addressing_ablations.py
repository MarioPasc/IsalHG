"""The three displaced fact addressings --- RQ1 arms C, D and D1.

The adopted encoding addresses a constant by its position in one global
canonical order (arm B, :mod:`isalhg.metric_space.distances.fact_levenshtein`).
These three arms replace that address with ``(key(c), index)``, where ``key``
is computed from the constant's own neighbourhood and ``index`` orders the
constants sharing a key by their canonical rank.  Each key is
isomorphism-invariant and the pair is injective by construction, so every arm
is a complete invariant --- they differ only in how a structural edit
propagates through the addresses, which is what RQ1 measures.

============================  ==================================================
arm / registered name         key ``kappa(c)``
============================  ==================================================
C / ``fact_local_colour``     the depth-3 WL colour of ``c`` --- *content*, a
                              global hash, so one fact edit moves almost every
                              colour
D / ``fact_local_key``        ``(type(c), sorted multiset over the facts
                              incident to c of (predicate, arity))`` --- strictly
                              depth 0: it reads ``c``'s own incidences and never
                              a neighbour's key
D1 / ``fact_degree_key``      ``(type(c), degree(c))`` --- the granularity
                              control; arm B is the degenerate single-class case
                              of the same family
============================  ==================================================

Word layout, identical across the three: an address-keyed type prefix
``T[addr; type]`` in increasing address order, then one ``F[l; addr_1 ...
addr_a]`` per fact with the operands sorted by address and the fact tokens
sorted lexicographically.  Because the address is written *inside* the token
rather than being the token's position, these words do not share the token
vocabulary of the adopted encoding and
:func:`isalhg.core.fact_word.decode_fact_word` does not read them.  They are
comparison arms, not a language.

Ported from ``scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/``
(``f4_encodings.word_C`` / ``local_addresses`` and ``f4_local_key.word_key``),
whose semantics are reproduced exactly.  ``rapidfuzz`` and ``pynauty`` are
reached only inside function bodies.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, TypeAlias

from isalhg.core.backends import Backend
from isalhg.core.fact_word import FACT_TAG, TYPE_TAG, Token, Word
from isalhg.core.hypergraph_wl import wl_hash
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import DistanceComputationError
from isalhg.metric_space.base import HypergraphDistance
from isalhg.metric_space.distances.fact_levenshtein import word_distance
from isalhg.metric_space.registry import register_distance
from isalhg.types import DistanceName, NodeId

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

Key: TypeAlias = tuple[Any, ...]
Address: TypeAlias = tuple[Key, int]

WL_DEPTH = 3

ARM_LOCAL_COLOUR = "local_colour"
ARM_LOCAL_KEY = "local_key"
ARM_DEGREE_KEY = "degree_key"

ARM_NAMES: dict[str, DistanceName] = {
    ARM_LOCAL_COLOUR: "fact_local_colour",
    ARM_LOCAL_KEY: "fact_local_key",
    ARM_DEGREE_KEY: "fact_degree_key",
}


# ---------------------------------------------------------------------------
# The three keys
# ---------------------------------------------------------------------------


def key_local_key(H: SparseHypergraph, v: NodeId) -> Key:
    """Return ``(type, sorted multiset of (predicate, arity) over v's facts)`` (arm D)."""
    return (
        H.vertex_label(v),
        tuple(sorted((H.edge_label(e), len(H.members(e))) for e in H.incident_edges(v))),
    )


def key_degree(H: SparseHypergraph, v: NodeId) -> Key:
    """Return ``(type, degree)`` (arm D1) --- the coarse control."""
    return (H.vertex_label(v), H.degree(v))


def _colour_keys(H: SparseHypergraph, backend: Backend | None) -> tuple[Key, ...]:
    """Return the depth-3 WL colour of every constant as a one-element key (arm C)."""
    colours = wl_hash(H, max_rounds=WL_DEPTH, backend=backend)
    return tuple((colour,) for colour in colours)


def keys_of(H: SparseHypergraph, arm: str, *, backend: Backend | None = None) -> tuple[Key, ...]:
    """Return the per-constant key of ``arm``.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.
    arm : {"local_colour", "local_key", "degree_key"}
        Which addressing to key by.
    backend : {"cpp", "python"} or None, optional
        Backend for the WL colour refinement; only arm ``"local_colour"`` uses
        it.  ``None`` takes the package default.

    Returns
    -------
    tuple[Key, ...]
        One key per constant, indexed by node id.

    Raises
    ------
    isalhg.errors.DistanceComputationError
        If ``arm`` is not one of the three names.
    """
    if arm == ARM_LOCAL_COLOUR:
        return _colour_keys(H, backend)
    plain: dict[str, Callable[[SparseHypergraph, NodeId], Key]] = {
        ARM_LOCAL_KEY: key_local_key,
        ARM_DEGREE_KEY: key_degree,
    }
    try:
        key_fn = plain[arm]
    except KeyError as exc:
        raise DistanceComputationError(
            f"unknown fact-addressing arm {arm!r}; expected one of {sorted(ARM_NAMES)}"
        ) from exc
    return tuple(key_fn(H, v) for v in range(H.n_nodes))


# ---------------------------------------------------------------------------
# Addressing and the word
# ---------------------------------------------------------------------------


def key_addresses(
    H: SparseHypergraph,
    arm: str,
    rank: Sequence[int] | None = None,
    *,
    backend: Backend | None = None,
) -> tuple[Address, ...]:
    """Return ``addr[v] = (kappa(v), index of v among the constants sharing kappa(v))``.

    The index orders same-key constants by their canonical rank, so the address
    map composes an isomorphism-invariant key with an isomorphism-invariant
    within-class order: it is itself isomorphism-invariant, and injective
    because the index is a position within its class.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.
    arm : {"local_colour", "local_key", "degree_key"}
        Which key to address by.
    rank : Sequence[int] or None, optional
        The canonical ranks; recomputed when ``None``.
    backend : {"cpp", "python"} or None, optional
        Backend for the WL colour refinement (arm ``"local_colour"`` only).

    Returns
    -------
    tuple[Address, ...]
        One address per constant, indexed by node id.
    """
    if rank is None:
        from isalhg.iso_backends.canonical_order import canonical_ranks

        rank = canonical_ranks(H)
    keys = keys_of(H, arm, backend=backend)
    by_key: dict[Key, list[NodeId]] = {}
    for v in range(H.n_nodes):
        by_key.setdefault(keys[v], []).append(v)
    addresses: list[Address] = [((), 0)] * H.n_nodes
    ranks = rank
    for key, members in by_key.items():
        for index, v in enumerate(sorted(members, key=lambda u: ranks[u])):
            addresses[v] = (key, index)
    return tuple(addresses)


def addressed_word(
    H: SparseHypergraph,
    arm: str,
    rank: Sequence[int] | None = None,
    *,
    backend: Backend | None = None,
) -> Word:
    """Return the fact word of ``H`` under the ``arm`` addressing.

    Parameters
    ----------
    H : SparseHypergraph
        The knowledge base.
    arm : {"local_colour", "local_key", "degree_key"}
        Which addressing to write.
    rank : Sequence[int] or None, optional
        The canonical ranks; recomputed when ``None``.
    backend : {"cpp", "python"} or None, optional
        Backend for the WL colour refinement (arm ``"local_colour"`` only).

    Returns
    -------
    Word
        ``n`` tokens ``("T", address, type)`` in increasing address order, then
        ``m`` tokens ``("F", predicate, address tuple)`` sorted lexicographically.
    """
    addresses = key_addresses(H, arm, rank, backend=backend)
    order = sorted(range(H.n_nodes), key=lambda v: addresses[v])
    prefix: list[Token] = [(TYPE_TAG, addresses[v], H.vertex_label(v)) for v in order]
    facts: list[Token] = []
    for _, members, label in H.iter_edges():
        facts.append((FACT_TAG, label, tuple(sorted(addresses[v] for v in members))))
    facts.sort(key=lambda token: (token[1], token[2]))
    return (*prefix, *facts)


def word_local_colour(H: SparseHypergraph, rank: Sequence[int] | None = None) -> Word:
    """Arm C --- addresses keyed by the depth-3 WL colour."""
    return addressed_word(H, ARM_LOCAL_COLOUR, rank)


def word_local_key(H: SparseHypergraph, rank: Sequence[int] | None = None) -> Word:
    """Arm D --- addresses keyed by ``(type, incident (predicate, arity) multiset)``."""
    return addressed_word(H, ARM_LOCAL_KEY, rank)


def word_degree_key(H: SparseHypergraph, rank: Sequence[int] | None = None) -> Word:
    """Arm D1 --- addresses keyed by ``(type, degree)``."""
    return addressed_word(H, ARM_DEGREE_KEY, rank)


# ---------------------------------------------------------------------------
# The distance
# ---------------------------------------------------------------------------


class FactAddressingAblation(HypergraphDistance):
    """Levenshtein distance between fact words under a displaced addressing.

    Parameters
    ----------
    arm : {"local_colour", "local_key", "degree_key"}
        Which addressing to use.
    backend : {"cpp", "python"} or None, optional
        Backend for the WL colour refinement (arm ``"local_colour"`` only).

    Raises
    ------
    isalhg.errors.DistanceComputationError
        If ``arm`` is not one of the three names.
    """

    def __init__(self, arm: str, *, backend: Backend | None = None) -> None:
        if arm not in ARM_NAMES:
            raise DistanceComputationError(
                f"unknown fact-addressing arm {arm!r}; expected one of {sorted(ARM_NAMES)}"
            )
        self._arm = arm
        self._backend = backend

    @property
    def name(self) -> DistanceName:
        return ARM_NAMES[self._arm]

    def pairwise(self, H1: SparseHypergraph, H2: SparseHypergraph) -> float:
        """Return the token-level edit distance between the two arm words."""
        w1 = addressed_word(H1, self._arm, backend=self._backend)
        w2 = addressed_word(H2, self._arm, backend=self._backend)
        return float(word_distance(w1, w2))

    def fingerprint(self, H: SparseHypergraph) -> Any | None:
        """Return the arm word of ``H``, the per-member object that amortizes :meth:`matrix`."""
        return addressed_word(H, self._arm, backend=self._backend)

    def matrix(self, corpus: Sequence[SparseHypergraph]) -> NDArray[np.float64]:
        """Return the dense distance matrix, writing each word once."""
        from isalhg.metric_space.distances.fact_levenshtein import _encode, _import_rapidfuzz

        levenshtein, process = _import_rapidfuzz()
        import numpy as np

        if not corpus:
            return np.zeros((0, 0), dtype=np.float64)
        encoded = _encode([addressed_word(H, self._arm, backend=self._backend) for H in corpus])
        result = process.cdist(encoded, encoded, scorer=levenshtein.distance, dtype=np.float64)
        return np.asarray(result, dtype=np.float64)


register_distance("fact_local_colour", lambda: FactAddressingAblation(ARM_LOCAL_COLOUR))
register_distance("fact_local_key", lambda: FactAddressingAblation(ARM_LOCAL_KEY))
register_distance("fact_degree_key", lambda: FactAddressingAblation(ARM_DEGREE_KEY))


__all__ = [
    "ARM_DEGREE_KEY",
    "ARM_LOCAL_COLOUR",
    "ARM_LOCAL_KEY",
    "ARM_NAMES",
    "Address",
    "FactAddressingAblation",
    "Key",
    "addressed_word",
    "key_addresses",
    "key_degree",
    "key_local_key",
    "keys_of",
    "word_degree_key",
    "word_local_colour",
    "word_local_key",
]
